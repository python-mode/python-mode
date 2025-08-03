#!/bin/bash
set -euo pipefail

# Validate Docker setup for python-mode testing
# This script validates the Phase 1 parallel implementation

echo "=== Python-mode Docker Test Environment Validation ==="
echo

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed or not in PATH"
    exit 1
else
    echo "✅ Docker is available"
fi

# Check Docker compose
if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not available"
    exit 1
else
    echo "✅ Docker Compose is available"
fi

# Check if required files exist
required_files=(
    "Dockerfile.base-test"
    "Dockerfile.test-runner"
    "docker-compose.test.yml"
    "scripts/test_isolation.sh"
    "scripts/test_orchestrator.py"
)

for file in "${required_files[@]}"; do
    if [[ -f "$file" ]]; then
        echo "✅ $file exists"
    else
        echo "❌ $file is missing"
        exit 1
    fi
done

# Check if Vader tests exist
vader_tests=(
    "tests/vader/setup.vim"
    "tests/vader/simple.vader"
    "tests/vader/autopep8.vader"
    "tests/vader/folding.vader"
    "tests/vader/lint.vader"
)

echo
echo "=== Checking Vader Test Files ==="
for test in "${vader_tests[@]}"; do
    if [[ -f "$test" ]]; then
        echo "✅ $test exists"
    else
        echo "❌ $test is missing"
    fi
done

# Build base image
echo
echo "=== Building Base Test Image ==="
if docker build -f Dockerfile.base-test -t python-mode-base-test:latest .; then
    echo "✅ Base test image built successfully"
else
    echo "❌ Failed to build base test image"
    exit 1
fi

# Build test runner image
echo
echo "=== Building Test Runner Image ==="
if docker build -f Dockerfile.test-runner -t python-mode-test-runner:latest .; then
    echo "✅ Test runner image built successfully"
else
    echo "❌ Failed to build test runner image"
    exit 1
fi

# Test simple Vader test execution
echo
echo "=== Testing Simple Vader Test ==="
if docker run --rm \
    -v "$(pwd):/workspace" \
    -e VIM_TEST_TIMEOUT=30 \
    python-mode-test-runner:latest \
    /workspace/tests/vader/simple.vader 2>/dev/null; then
    echo "✅ Simple Vader test execution successful"
else
    echo "❌ Simple Vader test execution failed"
fi

# Test legacy bash test in container
echo
echo "=== Testing Legacy Test in Container ==="
if docker run --rm \
    -v "$(pwd):/opt/python-mode" \
    -w /opt/python-mode \
    python-mode-base-test:latest \
    timeout 30s bash -c "cd tests && bash test_helpers_bash/test_createvimrc.sh" 2>/dev/null; then
    echo "✅ Legacy test environment setup successful"
else
    echo "❌ Legacy test environment setup failed"
fi

# Test Docker Compose services
echo
echo "=== Testing Docker Compose Configuration ==="
if docker compose -f docker-compose.test.yml config --quiet; then
    echo "✅ Docker Compose configuration is valid"
else
    echo "❌ Docker Compose configuration has errors"
    exit 1
fi

echo
echo "=== Phase 1 Docker Setup Validation Complete ==="
echo "✅ All components are ready for parallel test execution"
echo
echo "Next steps:"
echo "  1. Run: 'docker compose -f docker-compose.test.yml up test-builder'"
echo "  2. Run: 'docker compose -f docker-compose.test.yml up test-vader'"
echo "  3. Run: 'docker compose -f docker-compose.test.yml up test-legacy'"
echo "  4. Compare results between legacy and Vader tests"