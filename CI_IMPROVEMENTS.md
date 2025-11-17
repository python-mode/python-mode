# CI/CD Improvements: Multi-Platform Testing

This document describes the CI/CD improvements implemented to test python-mode on multiple platforms.

## Overview

The GitHub Actions CI workflow has been enhanced to test python-mode on **Linux**, **macOS**, and **Windows** platforms, ensuring compatibility across all major operating systems.

## Changes Made

### 1. Multi-Platform GitHub Actions Workflow

**File:** `.github/workflows/test.yml`

The workflow now includes three separate test jobs:

- **`test-linux`**: Tests on Ubuntu (Python 3.10, 3.11, 3.12, 3.13)
- **`test-macos`**: Tests on macOS (Python 3.10, 3.11, 3.12, 3.13)
- **`test-windows`**: Tests on Windows (Python 3.10, 3.11, 3.12, 3.13)

Each platform runs the full Vader test suite with all supported Python versions.

### 2. Windows PowerShell Test Script

**File:** `scripts/cicd/run_vader_tests_windows.ps1`

A new PowerShell script specifically designed for Windows CI environments:

- Handles Windows path separators (`\` vs `/`)
- Uses PowerShell-native commands and error handling
- Converts paths appropriately for Vim on Windows
- Generates JSON test results compatible with the existing summary system

**Key Features:**
- Automatic Vader.vim installation
- Windows-compatible vimrc generation
- Proper path handling for Windows filesystem
- JSON test results generation matching Linux/macOS format

### 3. Platform-Specific Setup

#### Linux (Ubuntu)
- Uses `vim-nox` package (installed via `apt-get`)
- Uses existing `run_vader_tests_direct.sh` bash script
- No changes required - already working

#### macOS
- Installs Vim via Homebrew (`brew install vim`)
- Uses existing `run_vader_tests_direct.sh` bash script
- Compatible with macOS filesystem (Unix-like)

#### Windows
- Installs Vim via Chocolatey (`choco install vim`)
- Uses new PowerShell script `run_vader_tests_windows.ps1`
- Handles Windows-specific path and shell differences

## Test Matrix

The CI now tests:

| Platform | Python Versions | Test Script |
|----------|----------------|-------------|
| Linux (Ubuntu) | 3.10, 3.11, 3.12, 3.13 | `run_vader_tests_direct.sh` |
| macOS | 3.10, 3.11, 3.12, 3.13 | `run_vader_tests_direct.sh` |
| Windows | 3.10, 3.11, 3.12, 3.13 | `run_vader_tests_windows.ps1` |

**Total:** 12 test configurations (3 platforms × 4 Python versions)

## Test Results

Test results are uploaded as artifacts with platform-specific naming:
- `test-results-linux-{python-version}`
- `test-results-macos-{python-version}`
- `test-results-windows-{python-version}`

The PR summary job aggregates results from all platforms and generates a comprehensive test summary.

## Benefits

1. **Cross-Platform Compatibility**: Ensures python-mode works correctly on all major operating systems
2. **Early Issue Detection**: Platform-specific issues are caught before release
3. **Better User Experience**: Users on Windows and macOS can be confident the plugin works on their platform
4. **Comprehensive Coverage**: Tests all supported Python versions on each platform

## Platform-Specific Considerations

### Windows
- Uses PowerShell for script execution
- Path separators converted for Vim compatibility
- Chocolatey used for Vim installation
- Windows-specific vimrc configuration

### macOS
- Uses Homebrew for package management
- Unix-like filesystem (compatible with Linux scripts)
- May have different Vim version than Linux

### Linux
- Standard Ubuntu package manager
- Reference platform (most thoroughly tested)
- Uses `vim-nox` for non-GUI Vim

## Running Tests Locally

### Linux/macOS
```bash
bash scripts/cicd/run_vader_tests_direct.sh
```

### Windows
```powershell
pwsh scripts/cicd/run_vader_tests_windows.ps1
```

## Troubleshooting

### Windows Issues

**Vim not found:**
- Ensure Chocolatey is available: `choco --version`
- Check PATH includes Vim installation directory
- Try refreshing PATH: `refreshenv` (if using Chocolatey)

**Path issues:**
- PowerShell script converts paths automatically
- Ensure vimrc uses forward slashes for runtime paths
- Check that project root path is correctly resolved

### macOS Issues

**Vim not found:**
- Ensure Homebrew is installed: `brew --version`
- Install Vim: `brew install vim`
- Check PATH includes `/usr/local/bin` or Homebrew bin directory

### General Issues

**Test failures:**
- Check Python version matches expected version
- Verify Ruff is installed: `ruff --version`
- Check Vader.vim is properly installed
- Review test logs in `test-logs/` directory

## Future Improvements

Potential enhancements:
- [ ] Test on Windows Server (in addition to Windows-latest)
- [ ] Test on specific macOS versions (e.g., macOS-12, macOS-13)
- [ ] Test with Neovim in addition to Vim
- [ ] Add performance benchmarks per platform
- [ ] Test with different Vim versions per platform

## Related Documentation

- **Migration Plan**: See `RUFF_MIGRATION_PLAN.md` Task 5.3
- **Test Scripts**: See `scripts/README.md`
- **Docker Testing**: See `README-Docker.md`

