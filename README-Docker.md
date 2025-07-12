# Docker Test Environment for python-mode

This directory contains Docker configuration to run python-mode tests in a containerized environment that matches the GitHub Actions CI environment.

## Prerequisites

- Docker
- Docker Compose

## Quick Start

### Run Tests

To run all tests in Docker (default version 3.13.0):

```bash
# Using the convenience script
./scripts/run-tests-docker.sh

# Or manually with docker-compose
docker compose run --rm python-mode-tests
```

### Interactive Development

To start an interactive shell for development:

```bash
docker compose run --rm python-mode-dev
```

## What's Included

The Docker environment includes:

- **Ubuntu 24.04** base image
- **pyenv** for Python version management
- **Multiple Python versions**: 3.10.13, 3.11.9, 3.12.4, 3.13.0
- **Python 3.13.0** as default
- **Vim built from source** with Python support for each Python version
- All required system dependencies:
  - GUI libraries (GTK, X11, etc.)
  - Lua 5.2
  - Perl
  - Build tools
  - Python build dependencies
- **python-mode plugin** properly installed and configured
- **Git submodules** initialized
- **Test environment** matching the CI setup

## Environment Details

The container replicates the GitHub Actions environment:

- Vim is built with `--enable-python3interp=yes` for each Python version
- pyenv is installed at `/opt/pyenv`
- Python versions are managed by pyenv:
  - 3.10.13
  - 3.11.9
  - 3.12.4
  - 3.13.0 (default)
- Each Python version has its own Vim binary: `vim-3.10.13`, `vim-3.11.9`, etc.
- Python config directory is automatically detected using `python-config --configdir`
- python-mode is installed in `/root/.vim/pack/foo/start/python-mode`
- Test configuration files are copied to the appropriate locations
- All required environment variables are set

## Test Execution

Tests are run using the same `tests/test.sh` script as in CI:

1. **test_autopep8.sh** - Tests automatic code formatting
2. **test_autocommands.sh** - Tests Vim autocommands
3. **test_folding.sh** - Tests code folding functionality
4. **test_textobject.sh** - Tests text object operations

## Testing with Different Python Versions

You can test python-mode with different Python versions:

```bash
# Test with Python 3.11.9
./scripts/run-tests-docker.sh 3.11

# Test with Python 3.12.4
./scripts/run-tests-docker.sh 3.12

# Test with Python 3.13.0
./scripts/run-tests-docker.sh 3.13
```

Available Python versions: 3.10.13, 3.11.9, 3.12.4, 3.13.0

Note: Use the major.minor format (e.g., 3.11) when specifying versions.

## Troubleshooting

### Python Config Directory Issues

The Dockerfile uses `python-config --configdir` to automatically detect the correct Python config directory. If you encounter issues:

1. Check that pyenv is properly initialized
2. Verify that the requested Python version is available
3. Ensure all environment variables are set correctly

### Build Failures

If the Docker build fails:

1. Check that all required packages are available in Ubuntu 24.04
2. Verify that pyenv can download and install Python versions
3. Ensure the Vim source code is accessible
4. Check that pyenv is properly initialized in the shell

### Test Failures

If tests fail in Docker but pass locally:

1. Check that the Vim build includes Python support for the correct version
2. Verify that all git submodules are properly initialized
3. Ensure the test environment variables are correctly set
4. Confirm that the correct Python version is active
5. Verify that pyenv is properly initialized

## Adding More Python Versions

To add support for additional Python versions:

1. Add the new version to the `pyenv install` commands in the Dockerfile.base
2. Update the test scripts to include the new version
4. Test that the new version works with the python-mode plugin
5. Update this documentation with the new version information 