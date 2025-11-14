#!/usr/bin/env python3
"""
Test Runner - Runs the Vader test suite
"""
import subprocess
import sys
import os
import json
import time
from pathlib import Path

def run_vader_tests():
    """Run the Vader test suite using the simple test runner"""
    print("⚡ Running Vader Test Suite...")
    try:
        # Use the Vader test runner which works in Docker
        root_dir = Path(__file__).parent.parent.parent
        test_script = root_dir / "scripts/user/run_tests.sh"
        
        if not test_script.exists():
            print(f"❌ Test script not found: {test_script}")
            return False
        
        # Ensure script is executable
        test_script.chmod(0o755)
        
        print(f"Executing: {test_script}")
        result = subprocess.run([
            "bash", str(test_script)
        ], 
        cwd=Path(__file__).parent.parent.parent,
        capture_output=True, 
        text=True, 
        timeout=300
        )
        
        print("Vader Test Output:")
        print(result.stdout)
        if result.stderr:
            print("Vader Test Errors:")
            print(result.stderr)
        
        # Log exit code for debugging
        print(f"Vader test runner exit code: {result.returncode}")
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ Vader tests timed out after 5 minutes")
        print("This may indicate hanging issues or very slow test execution")
        return False
    except FileNotFoundError as e:
        print(f"❌ Vader tests failed: Required file or command not found: {e}")
        return False
    except Exception as e:
        print(f"❌ Vader tests failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def generate_test_results(test_suite, vader_result):
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
        "results": {
            "vader": {
                "passed": vader_result,
                "test_type": test_suite
            }
        }
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
        f.write(f"Vader Tests: {'PASSED' if vader_result else 'FAILED'}\n")
    
    print(f"✅ Test results saved to test-results.json and test-logs/")

def main():
    """Run Vader test suite and report results"""
    print("🚀 Starting Vader Test Suite Execution")
    print("=" * 60)
    
    # Run tests based on TEST_SUITE environment variable
    test_suite = os.environ.get('TEST_SUITE', 'integration')
    
    # Run Vader tests
    vader_success = run_vader_tests()
    
    # Generate test results
    generate_test_results(test_suite, vader_success)
    
    print("\n" + "=" * 60)
    print("🎯 Test Results:")
    print(f"  Vader Tests: {'✅ PASSED' if vader_success else '❌ FAILED'}")
    
    if vader_success:
        print("🎉 ALL TESTS PASSED!")
        return 0
    else:
        print("⚠️ TESTS FAILED")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

