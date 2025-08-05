#!/usr/bin/env python3
import docker
import concurrent.futures
import json
import time
import signal
import sys
import os
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
import threading
import logging

# Add scripts directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    name: str
    status: str  # 'passed', 'failed', 'timeout', 'error'
    duration: float
    output: str
    error: Optional[str] = None
    metrics: Optional[Dict] = None

class TestOrchestrator:
    def __init__(self, max_parallel: int = 4, timeout: int = 60):
        self.client = docker.from_env()
        self.max_parallel = max_parallel
        self.timeout = timeout
        self.running_containers = set()
        self._lock = threading.Lock()
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._cleanup_handler)
        signal.signal(signal.SIGINT, self._cleanup_handler)
        
        # Ensure base images exist
        self._ensure_base_images()
    
    def _ensure_base_images(self):
        """Ensure required Docker images are available"""
        # Skip image check if running in test mode
        if os.environ.get('PYMODE_TEST_MODE', '').lower() == 'true':
            logger.info("Test mode enabled, skipping Docker image checks")
            return
            
        try:
            self.client.images.get('python-mode-test-runner:latest')
            logger.info("Found python-mode-test-runner:latest image")
        except docker.errors.ImageNotFound:
            logger.warning("python-mode-test-runner:latest not found, will attempt to build")
            # Try to build if Dockerfiles exist
            if Path('Dockerfile.test-runner').exists():
                logger.info("Building python-mode-test-runner:latest...")
                self.client.images.build(
                    path=str(Path.cwd()),
                    dockerfile='Dockerfile.test-runner',
                    tag='python-mode-test-runner:latest'
                )
            else:
                logger.error("Dockerfile.test-runner not found. Please build the test runner image first.")
                sys.exit(1)
    
    def run_test_suite(self, test_files: List[Path]) -> Dict[str, TestResult]:
        """Run a suite of tests in parallel"""
        results = {}
        logger.info(f"Starting test suite with {len(test_files)} tests, max parallel: {self.max_parallel}")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_parallel) as executor:
            future_to_test = {
                executor.submit(self._run_single_test, test): test 
                for test in test_files
            }
            
            for future in concurrent.futures.as_completed(future_to_test, timeout=300):
                test = future_to_test[future]
                try:
                    result = future.result()
                    results[str(test)] = result
                    logger.info(f"Test {test.name} completed: {result.status} ({result.duration:.2f}s)")
                except Exception as e:
                    logger.error(f"Test {test.name} failed with exception: {e}")
                    results[str(test)] = TestResult(
                        name=test.name,
                        status='error',
                        duration=0,
                        output='',
                        error=str(e)
                    )
        
        return results
    
    def _run_single_test(self, test_file: Path) -> TestResult:
        """Run a single test in a Docker container"""
        start_time = time.time()
        container = None
        monitor = None
        
        try:
            logger.debug(f"Starting test: {test_file.name}")
            
            # Create container with strict limits
            container = self.client.containers.run(
                'python-mode-test-runner:latest',
                command=[str(test_file)],
                detach=True,
                remove=False,  # We'll remove manually after getting logs
                mem_limit='256m',
                memswap_limit='256m',
                cpu_count=1,
                network_disabled=True,
                security_opt=['no-new-privileges:true'],
                read_only=True,
                tmpfs={
                    '/tmp': 'rw,noexec,nosuid,size=50m',
                    '/home/testuser/.vim': 'rw,noexec,nosuid,size=10m'
                },
                ulimits=[
                    docker.types.Ulimit(name='nproc', soft=32, hard=32),
                    docker.types.Ulimit(name='nofile', soft=512, hard=512)
                ],
                environment={
                    'VIM_TEST_TIMEOUT': str(self.timeout),
                    'PYTHONDONTWRITEBYTECODE': '1',
                    'PYTHONUNBUFFERED': '1',
                    'TEST_FILE': str(test_file)
                }
            )
            
            with self._lock:
                self.running_containers.add(container.id)
            
            # Start performance monitoring if available
            if PerformanceMonitor:
                monitor = PerformanceMonitor(container.id)
                monitor.start_monitoring(interval=0.5)
            
            # Wait with timeout
            result = container.wait(timeout=self.timeout)
            duration = time.time() - start_time
            
            # Get logs
            logs = container.logs(stdout=True, stderr=True).decode('utf-8', errors='replace')
            
            # Simple metrics only
            metrics = {'duration': duration}
            
            status = 'passed' if result['StatusCode'] == 0 else 'failed'
            
            return TestResult(
                name=test_file.name,
                status=status,
                duration=duration,
                output=logs,
                metrics=metrics
            )
            
        except docker.errors.ContainerError as e:
            return TestResult(
                name=test_file.name,
                status='failed',
                duration=time.time() - start_time,
                output=e.stderr.decode('utf-8', errors='replace') if e.stderr else '',
                error=str(e)
            )
        except Exception as e:
            return TestResult(
                name=test_file.name,
                status='timeout' if 'timeout' in str(e).lower() else 'error',
                duration=time.time() - start_time,
                output='',
                error=str(e)
            )
        finally:
            if container:
                with self._lock:
                    self.running_containers.discard(container.id)
                try:
                    container.remove(force=True)
                except:
                    pass
    
    def _parse_container_stats(self, stats: Dict) -> Dict:
        """Extract relevant metrics from container stats"""
        try:
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                       stats['precpu_stats']['cpu_usage']['total_usage']
            system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                          stats['precpu_stats']['system_cpu_usage']
            cpu_percent = (cpu_delta / system_delta) * 100.0 if system_delta > 0 else 0
            
            memory_usage = stats['memory_stats']['usage']
            memory_limit = stats['memory_stats']['limit']
            memory_percent = (memory_usage / memory_limit) * 100.0
            
            return {
                'cpu_percent': round(cpu_percent, 2),
                'memory_mb': round(memory_usage / 1024 / 1024, 2),
                'memory_percent': round(memory_percent, 2)
            }
        except:
            return {}
    
    def _cleanup_handler(self, signum, frame):
        """Clean up all running containers on exit"""
        logger.info("Cleaning up running containers...")
        with self._lock:
            for container_id in self.running_containers.copy():
                try:
                    container = self.client.containers.get(container_id)
                    container.kill()
                    container.remove()
                    logger.debug(f"Cleaned up container {container_id}")
                except:
                    pass
        sys.exit(0)

def find_test_files(test_dir: Path, patterns: List[str] = None) -> List[Path]:
    """Find test files in the given directory"""
    if patterns is None:
        patterns = ['*.vader']
    
    test_files = []
    for pattern in patterns:
        test_files.extend(test_dir.glob(pattern))
    
    return sorted(test_files)

def generate_summary_report(results: Dict[str, TestResult]) -> str:
    """Generate a summary report of test results"""
    total = len(results)
    passed = sum(1 for r in results.values() if r.status == 'passed')
    failed = sum(1 for r in results.values() if r.status == 'failed')
    errors = sum(1 for r in results.values() if r.status in ['timeout', 'error'])
    
    total_duration = sum(r.duration for r in results.values())
    avg_duration = total_duration / total if total > 0 else 0
    
    report = f"""
Test Summary:
=============
Total:    {total}
Passed:   {passed} ({passed/total*100:.1f}%)
Failed:   {failed} ({failed/total*100:.1f}%)
Errors:   {errors} ({errors/total*100:.1f}%)

Duration: {total_duration:.2f}s total, {avg_duration:.2f}s average

Results by status:
"""
    
    for status in ['failed', 'error', 'timeout']:
        status_tests = [name for name, r in results.items() if r.status == status]
        if status_tests:
            report += f"\n{status.upper()}:\n"
            for test in status_tests:
                report += f"  - {Path(test).name}\n"
    
    return report

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Run python-mode tests in Docker')
    parser.add_argument('tests', nargs='*', help='Specific tests to run')
    parser.add_argument('--parallel', type=int, default=4, help='Number of parallel tests')
    parser.add_argument('--timeout', type=int, default=60, help='Test timeout in seconds')
    parser.add_argument('--output', default='test-results.json', help='Output file')
    parser.add_argument('--test-dir', default='tests/vader', help='Test directory')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Find test files
    test_dir = Path(args.test_dir)
    if not test_dir.exists():
        logger.error(f"Test directory {test_dir} does not exist")
        sys.exit(1)
    
    if args.tests:
        test_files = []
        for test in args.tests:
            test_path = test_dir / test
            if not test_path.exists():
                test_path = Path(test)  # Try absolute path
            if test_path.exists():
                test_files.append(test_path)
            else:
                logger.error(f"Test file {test} not found")
                sys.exit(1)
    else:
        test_files = find_test_files(test_dir)
    
    if not test_files:
        logger.error("No test files found")
        sys.exit(1)
    
    logger.info(f"Found {len(test_files)} test files")
    
    # Run tests
    orchestrator = TestOrchestrator(max_parallel=args.parallel, timeout=args.timeout)
    results = orchestrator.run_test_suite(test_files)
    
    # Save results
    serializable_results = {
        test: {
            'name': result.name,
            'status': result.status,
            'duration': result.duration,
            'output': result.output,
            'error': result.error,
            'metrics': result.metrics
        }
        for test, result in results.items()
    }
    
    with open(args.output, 'w') as f:
        json.dump(serializable_results, f, indent=2)
    
    # Print summary
    summary = generate_summary_report(results)
    print(summary)
    
    # Save summary to markdown
    summary_file = Path(args.output).with_suffix('.md')
    with open(summary_file, 'w') as f:
        f.write(f"# Test Results\n\n{summary}\n")
    
    # Exit with appropriate code
    failed = sum(1 for r in results.values() if r.status == 'failed')
    errors = sum(1 for r in results.values() if r.status in ['timeout', 'error'])
    
    sys.exit(0 if failed == 0 and errors == 0 else 1)