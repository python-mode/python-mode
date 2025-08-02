#!/usr/bin/env python3
"""
Test script for Phase 2 implementation validation
"""
import sys
import subprocess
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_docker_availability():
    """Check if Docker is available and running"""
    try:
        result = subprocess.run(['docker', 'info'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            logger.info("Docker is available and running")
            return True
        else:
            logger.error(f"Docker info failed: {result.stderr}")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        logger.error(f"Docker check failed: {e}")
        return False

def check_base_images():
    """Check if required base Docker images exist"""
    try:
        result = subprocess.run(['docker', 'images', '--format', 'json'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            logger.error("Failed to list Docker images")
            return False
        
        images = []
        for line in result.stdout.strip().split('\n'):
            if line:
                images.append(json.loads(line))
        
        required_images = ['python-mode-base-test', 'python-mode-test-runner']
        available_images = [img['Repository'] for img in images]
        
        missing_images = []
        for required in required_images:
            if not any(required in img for img in available_images):
                missing_images.append(required)
        
        if missing_images:
            logger.warning(f"Missing Docker images: {missing_images}")
            logger.info("You may need to build the base images first")
            return False
        else:
            logger.info("Required Docker images are available")
            return True
            
    except Exception as e:
        logger.error(f"Error checking Docker images: {e}")
        return False

def test_orchestrator_import():
    """Test if the orchestrator can be imported and basic functionality works"""
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        import test_orchestrator
        TestOrchestrator = test_orchestrator.TestOrchestrator
        TestResult = test_orchestrator.TestResult
        
        # Test basic instantiation
        orchestrator = TestOrchestrator(max_parallel=1, timeout=30)
        logger.info("Orchestrator instantiated successfully")
        
        # Test TestResult dataclass
        result = TestResult(
            name="test",
            status="passed",
            duration=1.0,
            output="test output"
        )
        logger.info("TestResult dataclass works correctly")
        
        return True
        
    except Exception as e:
        logger.error(f"Orchestrator import/instantiation failed: {e}")
        return False

def test_performance_monitor_import():
    """Test if the performance monitor can be imported"""
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        import performance_monitor
        PerformanceMonitor = performance_monitor.PerformanceMonitor
        logger.info("Performance monitor imported successfully")
        return True
    except Exception as e:
        logger.error(f"Performance monitor import failed: {e}")
        return False

def check_vader_tests():
    """Check if Vader test files exist"""
    test_dir = Path('tests/vader')
    if not test_dir.exists():
        logger.error(f"Vader test directory {test_dir} does not exist")
        return False
    
    vader_files = list(test_dir.glob('*.vader'))
    if not vader_files:
        logger.error("No Vader test files found")
        return False
    
    logger.info(f"Found {len(vader_files)} Vader test files:")
    for f in vader_files:
        logger.info(f"  - {f.name}")
    
    return True

def run_simple_test():
    """Run a simple test with the orchestrator if possible"""
    if not check_docker_availability():
        logger.warning("Skipping Docker test due to unavailable Docker")
        return True
    
    if not check_base_images():
        logger.warning("Skipping Docker test due to missing base images")
        return True
    
    try:
        # Try to run a simple test
        test_dir = Path('tests/vader')
        if test_dir.exists():
            vader_files = list(test_dir.glob('*.vader'))
            if vader_files:
                # Use the first vader file for testing
                test_file = vader_files[0]
                logger.info(f"Running simple test with {test_file.name}")
                
                cmd = [
                    sys.executable, 
                    'scripts/test_orchestrator.py', 
                    '--parallel', '1',
                    '--timeout', '30',
                    '--output', '/tmp/phase2-test-results.json',
                    str(test_file.name)
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    logger.info("Simple orchestrator test passed")
                    return True
                else:
                    logger.error(f"Simple orchestrator test failed: {result.stderr}")
                    return False
    
    except Exception as e:
        logger.error(f"Simple test failed: {e}")
        return False
    
    return True

def main():
    """Main validation function"""
    logger.info("Starting Phase 2 validation")
    
    checks = [
        ("Docker availability", check_docker_availability),
        ("Orchestrator import", test_orchestrator_import),
        ("Performance monitor import", test_performance_monitor_import),
        ("Vader tests", check_vader_tests),
        ("Simple test run", run_simple_test)
    ]
    
    results = {}
    
    for check_name, check_func in checks:
        logger.info(f"Running check: {check_name}")
        try:
            results[check_name] = check_func()
        except Exception as e:
            logger.error(f"Check {check_name} failed with exception: {e}")
            results[check_name] = False
    
    # Summary
    logger.info("\n" + "="*50)
    logger.info("Phase 2 Validation Results:")
    logger.info("="*50)
    
    all_passed = True
    for check_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        logger.info(f"{check_name:.<30} {status}")
        if not passed:
            all_passed = False
    
    logger.info("="*50)
    
    if all_passed:
        logger.info("✅ Phase 2 validation PASSED - Ready for testing!")
    else:
        logger.warning("⚠️  Phase 2 validation had issues - Some features may not work")
        logger.info("Check the logs above for details on what needs to be fixed")
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())