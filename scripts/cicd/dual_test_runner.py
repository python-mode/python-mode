#!/usr/bin/env python3
"""
Simple Dual Test Runner - Runs both legacy bash tests and Vader tests
"""
import subprocess
import sys
import os
from pathlib import Path

def run_legacy_tests():
    """Run the legacy bash test suite using docker compose"""
    print("🔧 Running Legacy Bash Test Suite...")
    try:
        # Use the main docker-compose.yml with python-mode-tests service
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
            print("Legacy Test Errors:")
            print(result.stderr)
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ Legacy tests timed out")
        return False
    except Exception as e:
        print(f"❌ Legacy tests failed: {e}")
        return False

def run_vader_tests():
    """Run the Vader test suite using the run-vader-tests.sh script"""
    print("⚡ Running Vader Test Suite...")
    try:
        # Use the existing run-vader-tests.sh script which handles Docker setup
        result = subprocess.run([
            "bash", "scripts/user/run-vader-tests.sh"
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
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ Vader tests timed out")
        return False
    except Exception as e:
        print(f"❌ Vader tests failed: {e}")
        return False

def main():
    """Run both test suites and report results"""
    print("🚀 Starting Dual Test Suite Execution")
    print("=" * 60)
    
    # Run tests based on TEST_SUITE environment variable
    test_suite = os.environ.get('TEST_SUITE', 'integration')
    
    if test_suite == 'unit':
        # For unit tests, just run Vader tests
        vader_success = run_vader_tests()
        
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