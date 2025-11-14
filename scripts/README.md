# Scripts Directory Structure

This directory contains scripts for testing and CI/CD automation, organized into two categories:

## 📁 cicd/ - CI/CD Scripts

Scripts used by the GitHub Actions CI/CD pipeline:

- **run_vader_tests_direct.sh** - Direct Vader test runner for CI (no Docker)
  - Runs tests directly in GitHub Actions environment
  - Installs Vader.vim automatically
  - Generates test-results.json and logs

## 📁 user/ - User Scripts  

Scripts for local development and testing (using Docker):

- **run-tests-docker.sh** - Run tests with a specific Python version locally using Docker
- **run_tests.sh** - Run Vader test suite using Docker Compose
- **test-all-python-versions.sh** - Test against all supported Python versions

## Test Execution Paths

### Local Development (Docker)

For local development, use Docker Compose to run tests in a consistent environment:

```bash
# Test with default Python version (3.11)
./scripts/user/run-tests-docker.sh

# Test with specific Python version
./scripts/user/run-tests-docker.sh 3.11

# Test all Python versions
./scripts/user/test-all-python-versions.sh

# Run Vader tests using docker compose
./scripts/user/run_tests.sh

# Or directly with docker compose
docker compose run --rm python-mode-tests
```

### CI/CD (Direct Execution)

In GitHub Actions, tests run directly without Docker for faster execution:

- Uses `scripts/cicd/run_vader_tests_direct.sh`
- Automatically called by `.github/workflows/test.yml`
- No Docker build/pull overhead
- Same test coverage as local Docker tests

## Adding New Tests

To add new tests, simply create a new `.vader` file in `tests/vader/`. Both local Docker and CI test runners will automatically discover and run it.
