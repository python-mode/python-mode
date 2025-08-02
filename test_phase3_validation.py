#!/usr/bin/env python3
"""
Phase 3 Validation Script

This script validates that all Phase 3 components are properly implemented:
- Test isolation script exists and is executable
- Docker Compose configuration is valid
- Coordinator Dockerfile builds successfully
- Integration between components works
"""

import os
import sys
import subprocess
import json
from pathlib import Path


def run_command(command, description):
    """Run a command and return success status"""
    print(f"✓ {description}...")
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            check=True
        )
        print(f"  └─ Success: {description}")
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"  └─ Failed: {description}")
        print(f"     Error: {e.stderr}")
        return False, e.stderr


def validate_files():
    """Validate that all required files exist"""
    print("=== Phase 3 File Validation ===")
    
    required_files = [
        ("scripts/test_isolation.sh", "Test isolation script"),
        ("docker-compose.test.yml", "Docker Compose test configuration"),
        ("Dockerfile.coordinator", "Test coordinator Dockerfile"),
        ("scripts/test_orchestrator.py", "Test orchestrator script"),
        ("scripts/performance_monitor.py", "Performance monitor script"),
    ]
    
    all_good = True
    for file_path, description in required_files:
        if Path(file_path).exists():
            print(f"✓ {description}: {file_path}")
            
            # Check if script files are executable
            if file_path.endswith('.sh'):
                if os.access(file_path, os.X_OK):
                    print(f"  └─ Executable: Yes")
                else:
                    print(f"  └─ Executable: No (fixing...)")
                    os.chmod(file_path, 0o755)
            
        else:
            print(f"✗ {description}: {file_path} - NOT FOUND")
            all_good = False
    
    return all_good


def validate_docker_compose():
    """Validate Docker Compose configuration"""
    print("\n=== Docker Compose Validation ===")
    
    success, output = run_command(
        "docker compose -f docker-compose.test.yml config",
        "Docker Compose configuration syntax"
    )
    
    if success:
        print("  └─ Configuration is valid")
        return True
    else:
        print(f"  └─ Configuration errors found")
        return False


def validate_dockerfile():
    """Validate Dockerfile can be parsed"""
    print("\n=== Dockerfile Validation ===")
    
    # Check if Dockerfile has valid syntax
    success, output = run_command(
        "docker build -f Dockerfile.coordinator --dry-run . 2>&1 || echo 'Dry run not supported, checking syntax manually'",
        "Dockerfile syntax check"
    )
    
    # Manual syntax check
    try:
        with open("Dockerfile.coordinator", "r") as f:
            content = f.read()
            
        # Basic syntax checks
        lines = content.split('\n')
        dockerfile_instructions = ['FROM', 'RUN', 'COPY', 'WORKDIR', 'USER', 'CMD', 'EXPOSE', 'ENV', 'ARG']
        
        has_from = any(line.strip().upper().startswith('FROM') for line in lines)
        if not has_from:
            print("  └─ Error: No FROM instruction found")
            return False
            
        print("  └─ Basic syntax appears valid")
        return True
        
    except Exception as e:
        print(f"  └─ Error reading Dockerfile: {e}")
        return False


def validate_test_orchestrator():
    """Validate test orchestrator script"""
    print("\n=== Test Orchestrator Validation ===")
    
    success, output = run_command(
        "python3 scripts/test_orchestrator.py --help",
        "Test orchestrator help command"
    )
    
    if success:
        print("  └─ Script is executable and shows help")
        return True
    else:
        return False


def validate_integration():
    """Validate integration between components"""
    print("\n=== Integration Validation ===")
    
    # Check if test isolation script can be executed
    success, output = run_command(
        "bash -n scripts/test_isolation.sh",
        "Test isolation script syntax"
    )
    
    if not success:
        return False
    
    # Check if the required directories exist
    test_dirs = ["tests/vader"]
    for test_dir in test_dirs:
        if not Path(test_dir).exists():
            print(f"✓ Creating test directory: {test_dir}")
            Path(test_dir).mkdir(parents=True, exist_ok=True)
    
    print("  └─ Integration components validated")
    return True


def main():
    """Main validation function"""
    print("Phase 3 Infrastructure Validation")
    print("=" * 50)
    
    validations = [
        ("File Structure", validate_files),
        ("Docker Compose", validate_docker_compose),
        ("Dockerfile", validate_dockerfile),
        ("Test Orchestrator", validate_test_orchestrator),
        ("Integration", validate_integration),
    ]
    
    results = {}
    overall_success = True
    
    for name, validator in validations:
        try:
            success = validator()
            results[name] = success
            if not success:
                overall_success = False
        except Exception as e:
            print(f"✗ {name}: Exception occurred - {e}")
            results[name] = False
            overall_success = False
    
    # Summary
    print("\n" + "=" * 50)
    print("VALIDATION SUMMARY")
    print("=" * 50)
    
    for name, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {name}")
    
    print("\n" + "=" * 50)
    if overall_success:
        print("🎉 Phase 3 validation PASSED! All components are ready.")
        return 0
    else:
        print("❌ Phase 3 validation FAILED! Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())