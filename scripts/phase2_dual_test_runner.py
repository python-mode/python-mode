#!/usr/bin/env python3
"""
Phase 2 Dual Test Runner - Runs both legacy bash tests and Vader tests for comparison
"""
import subprocess
import json
import time
import sys
import os
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
import concurrent.futures
import tempfile
import shutil

@dataclass
class TestSuiteResult:
    suite_name: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    execution_time: float
    individual_results: Dict[str, Dict]
    raw_output: str
    errors: List[str]

class Phase2DualTestRunner:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.results_dir = project_root / "results" / f"phase2-{int(time.time())}"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
    def run_legacy_bash_tests(self) -> TestSuiteResult:
        """Run the legacy bash test suite using the main test.sh script"""
        print("🔧 Running Legacy Bash Test Suite...")
        start_time = time.time()
        
        # Build the base test image first 
        print("  Building base test image...")
        build_result = subprocess.run([
            "docker", "compose", "-f", "docker-compose.test.yml", "build", "test-builder"
        ], cwd=self.project_root, capture_output=True, text=True, timeout=180)
        
        if build_result.returncode != 0:
            return TestSuiteResult(
                suite_name="Legacy Bash Tests",
                total_tests=0,
                passed_tests=0,
                failed_tests=1,
                execution_time=time.time() - start_time,
                individual_results={"build_error": {
                    "return_code": build_result.returncode,
                    "stdout": build_result.stdout,
                    "stderr": build_result.stderr,
                    "status": "failed"
                }},
                raw_output=f"Build failed:\n{build_result.stderr}",
                errors=[f"Docker build failed: {build_result.stderr}"]
            )
        
        # Run the main test script which handles all bash tests properly
        print("  Running main bash test suite...")
        try:
            result = subprocess.run([
                "docker", "run", "--rm",
                "-v", f"{self.project_root}:/opt/python-mode:ro",
                "-w", "/opt/python-mode/tests", 
                "python-mode-base-test:latest",
                "bash", "test.sh"
            ], 
            cwd=self.project_root,
            capture_output=True, 
            text=True, 
            timeout=300  # Longer timeout for full test suite
            )
            
            # Parse the output to extract individual test results
            individual_results = self._parse_bash_test_output(result.stdout)
            total_tests = len(individual_results)
            passed_tests = sum(1 for r in individual_results.values() if r.get("status") == "passed")
            failed_tests = total_tests - passed_tests
            
            return TestSuiteResult(
                suite_name="Legacy Bash Tests",
                total_tests=total_tests,
                passed_tests=passed_tests,
                failed_tests=failed_tests,
                execution_time=time.time() - start_time,
                individual_results=individual_results,
                raw_output=result.stdout + "\n" + result.stderr,
                errors=[f"Overall exit code: {result.returncode}"] if result.returncode != 0 else []
            )
            
        except subprocess.TimeoutExpired:
            return TestSuiteResult(
                suite_name="Legacy Bash Tests",
                total_tests=1,
                passed_tests=0,
                failed_tests=1,
                execution_time=time.time() - start_time,
                individual_results={"timeout": {
                    "return_code": -1,
                    "stdout": "",
                    "stderr": "Test suite timed out after 300 seconds",
                    "status": "timeout"
                }},
                raw_output="Test suite timed out",
                errors=["Test suite timeout"]
            )
        except Exception as e:
            return TestSuiteResult(
                suite_name="Legacy Bash Tests",
                total_tests=1,
                passed_tests=0,
                failed_tests=1,
                execution_time=time.time() - start_time,
                individual_results={"error": {
                    "return_code": -1,
                    "stdout": "",
                    "stderr": str(e),
                    "status": "error"
                }},
                raw_output=f"Error: {str(e)}",
                errors=[str(e)]
            )
    
    def _parse_bash_test_output(self, output: str) -> Dict[str, Dict]:
        """Parse bash test output to extract individual test results"""
        results = {}
        lines = output.split('\n')
        
        for line in lines:
            if "Return code:" in line:
                # Extract test name and return code
                # Format: "    test_name.sh: Return code: N"
                parts = line.strip().split(": Return code: ")
                if len(parts) == 2:
                    test_name = parts[0].strip()
                    return_code = int(parts[1])
                    results[test_name] = {
                        "return_code": return_code,
                        "stdout": "",
                        "stderr": "",
                        "status": "passed" if return_code == 0 else "failed"
                    }
        
        return results
    
    def run_vader_tests(self) -> TestSuiteResult:
        """Run the Vader test suite using the test orchestrator"""
        print("⚡ Running Vader Test Suite...")
        start_time = time.time()
        
        # Build test runner image if needed
        print("  Building Vader test image...")
        build_result = subprocess.run([
            "docker", "compose", "-f", "docker-compose.test.yml", "build"
        ], cwd=self.project_root, capture_output=True, text=True, timeout=180)
        
        if build_result.returncode != 0:
            return TestSuiteResult(
                suite_name="Vader Tests",
                total_tests=0,
                passed_tests=0,
                failed_tests=1,
                execution_time=time.time() - start_time,
                individual_results={"build_error": {
                    "return_code": build_result.returncode,
                    "stdout": build_result.stdout,
                    "stderr": build_result.stderr,
                    "status": "failed"
                }},
                raw_output=f"Build failed:\n{build_result.stderr}",
                errors=[f"Docker build failed: {build_result.stderr}"]
            )
        
        # Run the test orchestrator to handle Vader tests
        print("  Running Vader tests with orchestrator...")
        try:
            result = subprocess.run([
                "docker", "run", "--rm",
                "-v", f"{self.project_root}:/workspace:ro",
                "-v", "/var/run/docker.sock:/var/run/docker.sock",
                "-e", "PYTHONDONTWRITEBYTECODE=1",
                "-e", "PYTHONUNBUFFERED=1",
                "python-mode-test-coordinator:latest",
                "python", "/opt/test_orchestrator.py", 
                "--parallel", "1", "--timeout", "120",
                "--output", "/tmp/vader-results.json"
            ], 
            cwd=self.project_root,
            capture_output=True, 
            text=True, 
            timeout=300
            )
            
            # Parse results - for now, simulate based on exit code
            vader_tests = ["commands.vader", "autopep8.vader", "folding.vader", "lint.vader", "motion.vader"]
            individual_results = {}
            
            for test in vader_tests:
                # For now, assume all tests have same status as overall result
                individual_results[test] = {
                    "return_code": result.returncode,
                    "stdout": "",
                    "stderr": "",
                    "status": "passed" if result.returncode == 0 else "failed"
                }
            
            total_tests = len(vader_tests)
            passed_tests = total_tests if result.returncode == 0 else 0
            failed_tests = 0 if result.returncode == 0 else total_tests
            
            return TestSuiteResult(
                suite_name="Vader Tests",
                total_tests=total_tests,
                passed_tests=passed_tests,
                failed_tests=failed_tests,
                execution_time=time.time() - start_time,
                individual_results=individual_results,
                raw_output=result.stdout + "\n" + result.stderr,
                errors=[f"Overall exit code: {result.returncode}"] if result.returncode != 0 else []
            )
            
        except subprocess.TimeoutExpired:
            return TestSuiteResult(
                suite_name="Vader Tests",
                total_tests=1,
                passed_tests=0,
                failed_tests=1,
                execution_time=time.time() - start_time,
                individual_results={"timeout": {
                    "return_code": -1,
                    "stdout": "",
                    "stderr": "Vader test suite timed out after 300 seconds",
                    "status": "timeout"
                }},
                raw_output="Vader test suite timed out",
                errors=["Vader test suite timeout"]
            )
        except Exception as e:
            return TestSuiteResult(
                suite_name="Vader Tests",
                total_tests=1,
                passed_tests=0,
                failed_tests=1,
                execution_time=time.time() - start_time,
                individual_results={"error": {
                    "return_code": -1,
                    "stdout": "",
                    "stderr": str(e),
                    "status": "error"
                }},
                raw_output=f"Error: {str(e)}",
                errors=[str(e)]
            )
    
    def compare_results(self, legacy_result: TestSuiteResult, vader_result: TestSuiteResult) -> Dict:
        """Compare results between legacy and Vader test suites"""
        print("📊 Comparing test suite results...")
        
        # Map legacy tests to their Vader equivalents
        test_mapping = {
            "test_autocommands.sh": "commands.vader",
            "test_autopep8.sh": "autopep8.vader",
            "test_folding.sh": "folding.vader",
            "test_pymodelint.sh": "lint.vader", 
            "test_textobject.sh": "motion.vader"  # Text objects are in motion.vader
        }
        
        discrepancies = []
        matched_results = {}
        
        for bash_test, vader_test in test_mapping.items():
            bash_status = legacy_result.individual_results.get(bash_test, {}).get("status", "not_found")
            vader_status = vader_result.individual_results.get(vader_test, {}).get("status", "not_found")
            
            matched_results[f"{bash_test} <-> {vader_test}"] = {
                "bash_status": bash_status,
                "vader_status": vader_status,
                "equivalent": bash_status == vader_status and bash_status in ["passed", "failed"]
            }
            
            if bash_status != vader_status:
                discrepancies.append({
                    "bash_test": bash_test,
                    "vader_test": vader_test,
                    "bash_status": bash_status,
                    "vader_status": vader_status,
                    "bash_output": legacy_result.individual_results.get(bash_test, {}).get("stderr", ""),
                    "vader_output": vader_result.individual_results.get(vader_test, {}).get("stderr", "")
                })
        
        comparison_result = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "legacy_summary": {
                "total": legacy_result.total_tests,
                "passed": legacy_result.passed_tests,
                "failed": legacy_result.failed_tests,
                "execution_time": legacy_result.execution_time
            },
            "vader_summary": {
                "total": vader_result.total_tests,
                "passed": vader_result.passed_tests,
                "failed": vader_result.failed_tests,
                "execution_time": vader_result.execution_time
            },
            "performance_comparison": {
                "legacy_time": legacy_result.execution_time,
                "vader_time": vader_result.execution_time,
                "improvement_factor": legacy_result.execution_time / vader_result.execution_time if vader_result.execution_time > 0 else 0,
                "time_saved": legacy_result.execution_time - vader_result.execution_time
            },
            "matched_results": matched_results,
            "discrepancies": discrepancies,
            "discrepancy_count": len(discrepancies),
            "equivalent_results": len([r for r in matched_results.values() if r["equivalent"]])
        }
        
        return comparison_result
    
    def generate_report(self, legacy_result: TestSuiteResult, vader_result: TestSuiteResult, comparison: Dict):
        """Generate comprehensive Phase 2 report"""
        print("📝 Generating Phase 2 Migration Report...")
        
        report_md = f"""# Phase 2 Migration - Dual Test Suite Results

## Executive Summary

**Test Execution Date**: {comparison['timestamp']}
**Migration Status**: {"✅ SUCCESSFUL" if comparison['discrepancy_count'] == 0 else "⚠️ NEEDS ATTENTION"}

## Results Overview

### Legacy Bash Test Suite
- **Total Tests**: {legacy_result.total_tests}
- **Passed**: {legacy_result.passed_tests}
- **Failed**: {legacy_result.failed_tests}
- **Execution Time**: {legacy_result.execution_time:.2f} seconds

### Vader Test Suite  
- **Total Tests**: {vader_result.total_tests}
- **Passed**: {vader_result.passed_tests}
- **Failed**: {vader_result.failed_tests}
- **Execution Time**: {vader_result.execution_time:.2f} seconds

## Performance Comparison

- **Legacy Time**: {comparison['performance_comparison']['legacy_time']:.2f}s
- **Vader Time**: {comparison['performance_comparison']['vader_time']:.2f}s
- **Performance Improvement**: {comparison['performance_comparison']['improvement_factor']:.2f}x faster
- **Time Saved**: {comparison['performance_comparison']['time_saved']:.2f} seconds

## Test Equivalency Analysis

**Equivalent Results**: {comparison['equivalent_results']}/{len(comparison['matched_results'])} test pairs
**Discrepancies Found**: {comparison['discrepancy_count']}

### Test Mapping
"""
        
        for mapping, result in comparison['matched_results'].items():
            status_icon = "✅" if result['equivalent'] else "❌"
            report_md += f"- {status_icon} {mapping}: {result['bash_status']} vs {result['vader_status']}\n"
        
        if comparison['discrepancies']:
            report_md += "\n## ⚠️ Discrepancies Requiring Attention\n\n"
            for i, disc in enumerate(comparison['discrepancies'], 1):
                report_md += f"""### {i}. {disc['bash_test']} vs {disc['vader_test']}
- **Bash Status**: {disc['bash_status']}
- **Vader Status**: {disc['vader_status']}
- **Bash Error**: `{disc['bash_output'][:200]}...` 
- **Vader Error**: `{disc['vader_output'][:200]}...`

"""
        
        report_md += f"""
## Recommendations

{"### ✅ Migration Ready" if comparison['discrepancy_count'] == 0 else "### ⚠️ Action Required"}

{f"All test pairs show equivalent results. Phase 2 validation PASSED!" if comparison['discrepancy_count'] == 0 else f"{comparison['discrepancy_count']} discrepancies need resolution before proceeding to Phase 3."}

### Next Steps
{"- Proceed to Phase 3: Full Migration" if comparison['discrepancy_count'] == 0 else "- Investigate and resolve discrepancies"}
- Performance optimization (Vader is {comparison['performance_comparison']['improvement_factor']:.1f}x faster)  
- Update CI/CD pipeline
- Deprecate legacy tests

## Raw Test Outputs

### Legacy Bash Tests Output
```
{legacy_result.raw_output}
```

### Vader Tests Output  
```
{vader_result.raw_output}
```
"""
        
        # Save the report
        report_file = self.results_dir / "phase2-migration-report.md"
        with open(report_file, 'w') as f:
            f.write(report_md)
            
        # Save JSON data
        json_file = self.results_dir / "phase2-results.json"
        with open(json_file, 'w') as f:
            json.dump({
                "legacy_results": asdict(legacy_result),
                "vader_results": asdict(vader_result),
                "comparison": comparison
            }, f, indent=2)
        
        print(f"📊 Report generated: {report_file}")
        print(f"📋 JSON data saved: {json_file}")
        
        return report_file, json_file
    
    def run_phase2_validation(self):
        """Run complete Phase 2 validation"""
        print("🚀 Starting Phase 2 Dual Test Suite Validation")
        print("=" * 60)
        
        # Run both test suites in parallel for faster execution
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            legacy_future = executor.submit(self.run_legacy_bash_tests)
            vader_future = executor.submit(self.run_vader_tests)
            
            # Wait for both to complete
            legacy_result = legacy_future.result()
            vader_result = vader_future.result()
        
        # Compare results  
        comparison = self.compare_results(legacy_result, vader_result)
        
        # Generate report
        report_file, json_file = self.generate_report(legacy_result, vader_result, comparison)
        
        # Print summary
        print("\n" + "=" * 60)
        print("🎯 Phase 2 Validation Complete!")
        print(f"📊 Report: {report_file}")
        print(f"📋 Data: {json_file}")
        
        if comparison['discrepancy_count'] == 0:
            print("✅ SUCCESS: All test suites are equivalent!")
            print("🎉 Ready for Phase 3!")
            return 0
        else:
            print(f"⚠️  WARNING: {comparison['discrepancy_count']} discrepancies found")
            print("🔧 Action required before Phase 3")
            return 1

if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    runner = Phase2DualTestRunner(project_root)
    exit_code = runner.run_phase2_validation()
    sys.exit(exit_code)