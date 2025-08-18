#!/usr/bin/env python3
"""
Simple Dual Test Runner - Runs both legacy bash tests and Vader tests
"""
import subprocess
import sys
import os
import json
import time
from pathlib import Path

def run_legacy_tests():
    """Run the legacy bash test suite using docker compose"""
    print("🔧 Running Legacy Bash Test Suite...")
    try:
        # Use the main docker-compose.yml with python-mode-tests service  
        # Note: The orphan container warning is harmless and can be ignored
        result = subprocess.run([
            "docker", "compose", "run", "--rm", "python-mode-tests"
        ], 
        cwd=Path(__file__).parent.parent.parent,
        capture_output=True, 
        text=True, 
        timeout=300
        )
        
        print("Legacy Test Output:")
        print(result.stdout)
        if result.stderr:
            # Filter out the harmless orphan container warning
            stderr_lines = result.stderr.split('\n')
            filtered_stderr = '\n'.join([
                line for line in stderr_lines 
                if 'orphan containers' not in line.lower()
            ])
            if filtered_stderr.strip():
                print("Legacy Test Errors:")
                print(filtered_stderr)
        
        # Check for "Return code: 1" or other non-zero return codes in output
        # This is needed because the test script itself may exit 0 even when tests fail
        if "Return code: 1" in result.stdout or "Return code: 2" in result.stdout:
            print("❌ Detected test failures in output")
            return False
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ Legacy tests timed out")
        return False
    except Exception as e:
        print(f"❌ Legacy tests failed: {e}")
        return False

def run_vader_tests():
    """Run the Vader test suite using the simple test runner"""
    print("⚡ Running Vader Test Suite...")
    try:
        # Use the Vader test runner which works in Docker
        root_dir = Path(__file__).parent.parent.parent
        test_script = root_dir / "scripts/user/run-vader-tests.sh"
        
        result = subprocess.run([
            "bash", str(test_script)
        ], 
        cwd=Path(__file__).parent.parent.parent,
        capture_output=True, 
        text=True, 
        timeout=600  # Increased timeout for Vader tests
        )
        
        print("Vader Test Output:")
        print(result.stdout)
        if result.stderr:
            print("Vader Test Errors:")
            print(result.stderr)
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ Vader tests timed out")
        return False
    except Exception as e:
        print(f"❌ Vader tests failed: {e}")
        return False

def generate_test_results(test_suite, legacy_result=None, vader_result=None):
    """Generate test result artifacts for CI"""
    # Create results directory
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    
    # Create test-logs directory
    logs_dir = Path("test-logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Generate test results JSON
    test_results = {
        "timestamp": time.time(),
        "test_suite": test_suite,
        "python_version": os.environ.get("PYTHON_VERSION", "unknown"),
        "results": {}
    }
    
    if test_suite == "unit":
        test_results["results"]["vader"] = {
            "passed": vader_result if vader_result is not None else False,
            "test_type": "unit"
        }
    elif test_suite == "integration":
        test_results["results"]["legacy"] = {
            "passed": legacy_result if legacy_result is not None else False,
            "test_type": "integration"
        }
        test_results["results"]["vader"] = {
            "passed": vader_result if vader_result is not None else False,
            "test_type": "integration"
        }
    
    # Write test results JSON
    with open("test-results.json", "w") as f:
        json.dump(test_results, f, indent=2)
    
    # Create a summary log file
    with open(logs_dir / "test-summary.log", "w") as f:
        f.write(f"Test Suite: {test_suite}\n")
        f.write(f"Python Version: {os.environ.get('PYTHON_VERSION', 'unknown')}\n")
        f.write(f"Timestamp: {time.ctime()}\n")
        f.write("=" * 60 + "\n")
        
        if legacy_result is not None:
            f.write(f"Legacy Tests: {'PASSED' if legacy_result else 'FAILED'}\n")
        if vader_result is not None:
            f.write(f"Vader Tests: {'PASSED' if vader_result else 'FAILED'}\n")
    
    print(f"✅ Test results saved to test-results.json and test-logs/")

def main():
    """Run both test suites and report results"""
    print("🚀 Starting Dual Test Suite Execution")
    print("=" * 60)
    
    # Run tests based on TEST_SUITE environment variable
    test_suite = os.environ.get('TEST_SUITE', 'integration')
    
    if test_suite == 'unit':
        # For unit tests, just run Vader tests
        vader_success = run_vader_tests()
        
        # Generate test results
        generate_test_results(test_suite, vader_result=vader_success)
        
        if vader_success:
            print("✅ Unit tests (Vader) PASSED")
            return 0
        else:
            print("❌ Unit tests (Vader) FAILED")
            return 1
            
    elif test_suite == 'integration':
        # For integration tests, run both legacy and Vader
        legacy_success = run_legacy_tests()
        vader_success = run_vader_tests()
        
        # Generate test results
        generate_test_results(test_suite, legacy_result=legacy_success, vader_result=vader_success)
        
        print("\n" + "=" * 60)
        print("🎯 Dual Test Results:")
        print(f"  Legacy Tests: {'✅ PASSED' if legacy_success else '❌ FAILED'}")
        print(f"  Vader Tests:  {'✅ PASSED' if vader_success else '❌ FAILED'}")
        
        if legacy_success and vader_success:
            print("🎉 ALL TESTS PASSED!")
            return 0
        else:
            print("⚠️ SOME TESTS FAILED")
            return 1
    else:
        print(f"Unknown test suite: {test_suite}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)