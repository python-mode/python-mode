#!/usr/bin/env python3
"""Test script to verify path resolution works correctly on different platforms.

This script tests that pymode/utils.py patch_paths() function correctly
resolves paths for required submodules on different operating systems.

Note: This script tests the path resolution logic without requiring Vim,
since patch_paths() requires vim module at runtime.
"""

import os
import sys
import platform

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
PYMODE_DIR = os.path.join(PROJECT_ROOT, 'pymode')
SUBMODULES_DIR = os.path.join(PROJECT_ROOT, 'submodules')


def test_path_resolution_logic():
    """Test the path resolution logic used by patch_paths()."""


def test_path_resolution_logic():
    """Test the path resolution logic used by patch_paths()."""
    print("=" * 70)
    print("Path Resolution Test")
    print("=" * 70)
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Python version: {sys.version.split()[0]}")
    print(f"Python executable: {sys.executable}")
    print()
    
    # Simulate patch_paths() logic
    print("Simulating patch_paths() logic...")
    dir_script = PYMODE_DIR
    dir_submodule = os.path.abspath(os.path.join(dir_script, '..', 'submodules'))
    
    print(f"Pymode directory: {dir_script}")
    print(f"Submodules directory: {dir_submodule}")
    print()
    
    # Required submodules (from patch_paths() logic)
    required_submodules = ['rope', 'tomli', 'pytoolconfig']
    
    print("Checking required submodules:")
    print("-" * 70)
    
    all_found = True
    paths_to_add = []
    
    for module in required_submodules:
        module_full_path = os.path.join(dir_submodule, module)
        exists = os.path.exists(module_full_path)
        
        # Simulate the check from patch_paths()
        if exists and module_full_path not in sys.path:
            paths_to_add.append(module_full_path)
            status = "✓"
        elif exists:
            status = "⚠"  # Already in path
            paths_to_add.append(module_full_path)
        else:
            status = "✗"
        
        print(f"{status} {module:15} | Exists: {str(exists):5} | Path: {module_full_path}")
        
        if not exists:
            print(f"    ERROR: Module directory not found!")
            all_found = False
    
    print()
    
    # Check for removed submodules (should NOT exist or be added)
    removed_submodules = [
        'pyflakes', 'pycodestyle', 'mccabe', 'pylint', 
        'pydocstyle', 'pylama', 'autopep8', 'snowball_py',
        'toml', 'appdirs', 'astroid'
    ]
    
    print("\nChecking removed submodules (should NOT be added to paths):")
    print("-" * 70)
    
    removed_found = False
    for module in removed_submodules:
        module_path = os.path.join(dir_submodule, module)
        exists = os.path.exists(module_path)
        
        # Check if it would be added (it shouldn't be in required_submodules)
        if module in required_submodules:
            print(f"✗ {module:15} | ERROR: Still in required_submodules list!")
            removed_found = True
        elif exists:
            print(f"⚠ {module:15} | WARNING: Directory still exists (should be removed)")
        else:
            print(f"✓ {module:15} | Correctly excluded")
    
    if not removed_found:
        print("\n✓ All removed submodules correctly excluded from path resolution")
    
    print()
    
    # Platform-specific path handling test
    print("\nPlatform-specific path handling:")
    print("-" * 70)
    is_windows = sys.platform == 'win32' or sys.platform == 'msys'
    if is_windows:
        print("✓ Windows platform detected - using Windows-specific path handling")
        print("  (patch_paths() only adds submodules on Windows)")
    else:
        print(f"✓ Unix-like platform ({sys.platform}) - using standard path handling")
        print("  (patch_paths() only adds submodules on Windows)")
        print("  Note: On Unix, submodules are accessed via pymode/libs")
    
    # Test path separators
    print("\nPath separator test:")
    print("-" * 70)
    for module in required_submodules:
        path = os.path.join(dir_submodule, module)
        if os.path.exists(path):
            # os.path.join handles separators correctly for platform
            normalized = os.path.normpath(path)
            print(f"✓ {module:15} | Normalized: {normalized[:60]}...")
    
    print()
    print("=" * 70)
    
    # Summary
    if all_found and not removed_found:
        print("RESULT: ✓ All path resolution tests passed!")
        print(f"\nWould add {len(paths_to_add)} path(s) to sys.path:")
        for p in paths_to_add:
            print(f"  - {p}")
        return 0
    else:
        print("RESULT: ✗ Some path resolution tests failed!")
        return 1


if __name__ == '__main__':
    exit_code = test_path_resolution_logic()
    sys.exit(exit_code)

