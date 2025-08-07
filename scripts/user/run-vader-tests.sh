#!/bin/bash
set -euo pipefail

# Simple test runner for Vader tests using Docker
# This script demonstrates Phase 1 implementation

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

# Show usage
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS] [TEST_FILES...]

Run python-mode Vader tests in Docker containers.

OPTIONS:
    --help, -h          Show this help message
    --build             Build Docker images before running tests
    --verbose, -v       Enable verbose output
    --timeout SECONDS   Set test timeout (default: 60)
    --python VERSION    Python version to use (default: 3.11)
    --vim VERSION       Vim version to use (default: 9.0)
    --parallel JOBS     Number of parallel test jobs (default: 1)

EXAMPLES:
    $0                                  # Run all tests
    $0 --build                          # Build images and run all tests
    $0 tests/vader/autopep8.vader       # Run specific test
    $0 --verbose --timeout 120          # Run with verbose output and longer timeout
    $0 --python 3.12 --parallel 4      # Run with Python 3.12 using 4 parallel jobs

ENVIRONMENT VARIABLES:
    PYTHON_VERSION      Python version to use
    VIM_VERSION         Vim version to use  
    VIM_TEST_TIMEOUT    Test timeout in seconds
    VIM_TEST_VERBOSE    Enable verbose output (1/0)
    TEST_PARALLEL_JOBS  Number of parallel jobs
EOF
}

# Default values
BUILD_IMAGES=false
VERBOSE=0
TIMEOUT=60
PYTHON_VERSION="${PYTHON_VERSION:-3.11}"
VIM_VERSION="${VIM_VERSION:-9.0}"
PARALLEL_JOBS="${TEST_PARALLEL_JOBS:-1}"
TEST_FILES=()

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_usage
            exit 0
            ;;
        --build)
            BUILD_IMAGES=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=1
            shift
            ;;
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        --python)
            PYTHON_VERSION="$2"
            shift 2
            ;;
        --vim)
            VIM_VERSION="$2"
            shift 2
            ;;
        --parallel)
            PARALLEL_JOBS="$2"
            shift 2
            ;;
        -*)
            log_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
        *)
            TEST_FILES+=("$1")
            shift
            ;;
    esac
done

# Validate arguments
if ! [[ "$TIMEOUT" =~ ^[0-9]+$ ]] || [[ "$TIMEOUT" -lt 1 ]]; then
    log_error "Invalid timeout value: $TIMEOUT"
    exit 1
fi

if ! [[ "$PARALLEL_JOBS" =~ ^[0-9]+$ ]] || [[ "$PARALLEL_JOBS" -lt 1 ]]; then
    log_error "Invalid parallel jobs value: $PARALLEL_JOBS"
    exit 1
fi

# Set environment variables
export PYTHON_VERSION
export VIM_VERSION
export VIM_TEST_TIMEOUT="$TIMEOUT"
export VIM_TEST_VERBOSE="$VERBOSE"
export TEST_PARALLEL_JOBS="$PARALLEL_JOBS"

log_info "Starting Vader test runner"
log_info "Python: $PYTHON_VERSION, Vim: $VIM_VERSION, Timeout: ${TIMEOUT}s, Parallel: $PARALLEL_JOBS"

# Check Docker availability
if ! command -v docker >/dev/null 2>&1; then
    log_error "Docker is not installed or not in PATH"
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    log_error "Docker daemon is not running or not accessible"
    exit 1
fi

# Build images if requested
if [[ "$BUILD_IMAGES" == "true" ]]; then
    log_info "Building Docker images..."
    
    log_info "Building test image..."
    if ! docker compose build python-mode-tests; then
        log_error "Failed to build test image"
        exit 1
    fi
    
    log_success "Docker images built successfully"
fi

# Find test files if none specified
if [[ ${#TEST_FILES[@]} -eq 0 ]]; then
    if [[ -d "tests/vader" ]]; then
        mapfile -t TEST_FILES < <(find tests/vader -name "*.vader" -type f | sort)
    else
        log_warning "No tests/vader directory found, creating example test..."
        mkdir -p tests/vader
        cat > tests/vader/example.vader << 'EOF'
" Example Vader test
Include: setup.vim

Execute (Simple test):
  Assert 1 == 1, 'Basic assertion should pass'

Given python (Simple Python code):
  print("Hello, World!")

Then (Check content):
  AssertEqual ['print("Hello, World!")'], getline(1, '$')
EOF
        TEST_FILES=("tests/vader/example.vader")
        log_info "Created example test: tests/vader/example.vader"
    fi
fi

if [[ ${#TEST_FILES[@]} -eq 0 ]]; then
    log_error "No test files found"
    exit 1
fi

log_info "Found ${#TEST_FILES[@]} test file(s)"

# Run tests
FAILED_TESTS=()
PASSED_TESTS=()
TOTAL_DURATION=0

run_single_test() {
    local test_file="$1"
    local test_name=$(basename "$test_file" .vader)
    local start_time=$(date +%s)
    
    log_info "Running test: $test_name"
    
    # Create unique container name
    local container_name="pymode-test-${test_name}-$$-$(date +%s)"
    
    # Run test in container
    local exit_code=0
    if [[ "$VERBOSE" == "1" ]]; then
        docker run --rm \
            --name "$container_name" \
            --memory=256m \
            --cpus=1 \
            --network=none \
            --security-opt=no-new-privileges:true \
            --read-only \
            --tmpfs /tmp:rw,noexec,nosuid,size=50m \
            --tmpfs /home/testuser/.vim:rw,noexec,nosuid,size=10m \
            -e VIM_TEST_TIMEOUT="$TIMEOUT" \
            -e VIM_TEST_VERBOSE=1 \
            "python-mode-test-runner:${PYTHON_VERSION}-${VIM_VERSION}" \
            "$test_file" || exit_code=$?
    else
        docker run --rm \
            --name "$container_name" \
            --memory=256m \
            --cpus=1 \
            --network=none \
            --security-opt=no-new-privileges:true \
            --read-only \
            --tmpfs /tmp:rw,noexec,nosuid,size=50m \
            --tmpfs /home/testuser/.vim:rw,noexec,nosuid,size=10m \
            -e VIM_TEST_TIMEOUT="$TIMEOUT" \
            -e VIM_TEST_VERBOSE=0 \
            "python-mode-test-runner:${PYTHON_VERSION}-${VIM_VERSION}" \
            "$test_file" >/dev/null 2>&1 || exit_code=$?
    fi
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    TOTAL_DURATION=$((TOTAL_DURATION + duration))
    
    if [[ $exit_code -eq 0 ]]; then
        log_success "Test passed: $test_name (${duration}s)"
        PASSED_TESTS+=("$test_name")
    else
        if [[ $exit_code -eq 124 ]]; then
            log_error "Test timed out: $test_name (${TIMEOUT}s)"
        else
            log_error "Test failed: $test_name (exit code: $exit_code, ${duration}s)"
        fi
        FAILED_TESTS+=("$test_name")
    fi
    
    return $exit_code
}

# Run tests (sequentially for now, parallel execution in Phase 2)
log_info "Running tests..."
for test_file in "${TEST_FILES[@]}"; do
    if [[ ! -f "$test_file" ]]; then
        log_warning "Test file not found: $test_file"
        continue
    fi
    
    run_single_test "$test_file"
done

# Generate summary report
echo
log_info "Test Summary"
log_info "============"
log_info "Total tests: ${#TEST_FILES[@]}"
log_info "Passed: ${#PASSED_TESTS[@]}"
log_info "Failed: ${#FAILED_TESTS[@]}"
log_info "Total duration: ${TOTAL_DURATION}s"

if [[ ${#PASSED_TESTS[@]} -gt 0 ]]; then
    echo
    log_success "Passed tests:"
    for test in "${PASSED_TESTS[@]}"; do
        echo "  ✓ $test"
    done
fi

if [[ ${#FAILED_TESTS[@]} -gt 0 ]]; then
    echo
    log_error "Failed tests:"
    for test in "${FAILED_TESTS[@]}"; do
        echo "  ✗ $test"
    done
    echo
    log_error "Some tests failed. Check the output above for details."
    exit 1
else
    echo
    log_success "All tests passed!"
    exit 0
fi