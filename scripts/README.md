# Scripts Directory Structure

This directory contains scripts for testing and CI/CD automation, organized into two categories:

## 📁 cicd/ - CI/CD Scripts

Scripts used by the GitHub Actions CI/CD pipeline:

- **check_python_docker_image.sh** - Handles Python version resolution (especially for Python 3.13)
- **run_tests.py** - Runs the Vader test suite (legacy bash tests have been migrated to Vader)
- **generate_test_report.py** - Generates HTML/Markdown test reports for CI/CD

## 📁 user/ - User Scripts  

Scripts for local development and testing:

- **run-tests-docker.sh** - Run tests with a specific Python version locally
- **run_tests.sh** - Run Vader test suite (also used by run_tests.py)
- **test-all-python-versions.sh** - Test against all supported Python versions

## Usage Examples

### Local Testing

```bash
# Test with default Python version
./scripts/user/run-tests-docker.sh

# Test with specific Python version
./scripts/user/run-tests-docker.sh 3.11

# Test all Python versions
./scripts/user/test-all-python-versions.sh

# Run only Vader tests
./scripts/user/run_tests.sh
```

### CI/CD (automated)

The CI/CD scripts are automatically called by GitHub Actions workflows and typically don't need manual execution.
