#!/bin/bash
set -euo pipefail

# Phase 1 validation script
# Tests the basic Docker infrastructure and Vader integration

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

# Track validation results
VALIDATION_RESULTS=()
FAILED_VALIDATIONS=()

validate_step() {
    local step_name="$1"
    local step_description="$2"
    shift 2
    
    log_info "Validating: $step_description"
    
    if "$@"; then
        log_success "✓ $step_name"
        VALIDATION_RESULTS+=("✓ $step_name")
        return 0
    else
        log_error "✗ $step_name"
        VALIDATION_RESULTS+=("✗ $step_name")
        FAILED_VALIDATIONS+=("$step_name")
        return 1
    fi
}

# Validation functions
check_docker_available() {
    command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1
}

check_docker_compose_available() {
    command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1
}

check_dockerfiles_exist() {
    [[ -f "Dockerfile.base-test" ]] && [[ -f "Dockerfile.test-runner" ]]
}

check_docker_compose_config() {
    [[ -f "docker-compose.test.yml" ]] && docker compose -f docker-compose.test.yml config >/dev/null 2>&1
}

check_test_scripts_exist() {
    [[ -f "scripts/test-isolation.sh" ]] && [[ -f "scripts/vim-test-wrapper.sh" ]] && [[ -f "scripts/run-vader-tests.sh" ]]
}

check_test_scripts_executable() {
    [[ -x "scripts/test-isolation.sh" ]] && [[ -x "scripts/vim-test-wrapper.sh" ]] && [[ -x "scripts/run-vader-tests.sh" ]]
}

check_vader_tests_exist() {
    [[ -d "tests/vader" ]] && [[ -f "tests/vader/setup.vim" ]] && ls tests/vader/*.vader >/dev/null 2>&1
}

build_base_image() {
    log_info "Building base test image..."
    export PYTHON_VERSION=3.11
    export VIM_VERSION=9.0
    docker compose -f docker-compose.test.yml build base-test >/dev/null 2>&1
}

build_test_runner_image() {
    log_info "Building test runner image..."
    export PYTHON_VERSION=3.11
    export VIM_VERSION=9.0
    docker compose -f docker-compose.test.yml build test-runner >/dev/null 2>&1
}

test_container_creation() {
    log_info "Testing container creation..."
    local container_id
    container_id=$(docker run -d --rm \
        --memory=256m \
        --cpus=1 \
        --network=none \
        --security-opt=no-new-privileges:true \
        --read-only \
        --tmpfs /tmp:rw,noexec,nosuid,size=50m \
        --tmpfs /home/testuser/.vim:rw,noexec,nosuid,size=10m \
        python-mode-test-runner:3.11-9.0 \
        sleep 10)
    
    if [[ -n "$container_id" ]]; then
        docker kill "$container_id" >/dev/null 2>&1 || true
        return 0
    else
        return 1
    fi
}

test_vim_execution() {
    log_info "Testing vim execution in container..."
    docker run --rm \
        --memory=256m \
        --cpus=1 \
        --network=none \
        --security-opt=no-new-privileges:true \
        --read-only \
        --tmpfs /tmp:rw,noexec,nosuid,size=50m \
        --tmpfs /home/testuser/.vim:rw,noexec,nosuid,size=10m \
        -e VIM_TEST_TIMEOUT=10 \
        --entrypoint=/bin/bash \
        python-mode-test-runner:3.11-9.0 \
        -c 'timeout 5s vim -X -N -u NONE -c "quit!" >/dev/null 2>&1'
}

test_simple_vader_test() {
    log_info "Testing simple Vader test execution..."
    
    # Use the simple test file
    local test_file="tests/vader/simple.vader"
    
    if [[ ! -f "$test_file" ]]; then
        log_error "Test file not found: $test_file"
        return 1
    fi
    
    # Run the test without tmpfs on .vim directory to preserve plugin structure
    docker run --rm \
        --memory=256m \
        --cpus=1 \
        --network=none \
        --security-opt=no-new-privileges:true \
        --read-only \
        --tmpfs /tmp:rw,noexec,nosuid,size=50m \
        -e VIM_TEST_TIMEOUT=15 \
        -e VIM_TEST_VERBOSE=0 \
        python-mode-test-runner:3.11-9.0 \
        "$test_file" >/dev/null 2>&1
}

# Main validation process
main() {
    log_info "Starting Phase 1 validation"
    log_info "============================"
    
    # Basic environment checks
    validate_step "docker-available" "Docker is available and running" check_docker_available
    validate_step "docker-compose-available" "Docker Compose is available" check_docker_compose_available
    validate_step "dockerfiles-exist" "Dockerfiles exist" check_dockerfiles_exist
    validate_step "docker-compose-config" "Docker Compose configuration is valid" check_docker_compose_config
    validate_step "test-scripts-exist" "Test scripts exist" check_test_scripts_exist
    validate_step "test-scripts-executable" "Test scripts are executable" check_test_scripts_executable
    validate_step "vader-tests-exist" "Vader tests exist" check_vader_tests_exist
    
    # Build and test Docker images
    validate_step "build-base-image" "Base Docker image builds successfully" build_base_image
    validate_step "build-test-runner-image" "Test runner Docker image builds successfully" build_test_runner_image
    
    # Container functionality tests
    validate_step "container-creation" "Containers can be created with security restrictions" test_container_creation
    validate_step "vim-execution" "Vim executes successfully in container" test_vim_execution
    validate_step "vader-test-execution" "Simple Vader test executes successfully" test_simple_vader_test
    
    # Generate summary report
    echo
    log_info "Validation Summary"
    log_info "=================="
    
    for result in "${VALIDATION_RESULTS[@]}"; do
        echo "  $result"
    done
    
    echo
    if [[ ${#FAILED_VALIDATIONS[@]} -eq 0 ]]; then
        log_success "All validations passed! Phase 1 implementation is working correctly."
        log_info "You can now run tests using: ./scripts/run-vader-tests.sh --build"
        return 0
    else
        log_error "Some validations failed:"
        for failed in "${FAILED_VALIDATIONS[@]}"; do
            echo "  - $failed"
        done
        echo
        log_error "Please fix the issues above before proceeding."
        return 1
    fi
}

# Cleanup function
cleanup() {
    log_info "Cleaning up validation artifacts..."
    
    # Remove validation test file
    rm -f tests/vader/validation.vader 2>/dev/null || true
    
    # Clean up any leftover containers
    docker ps -aq --filter "name=pymode-test-validation" | xargs -r docker rm -f >/dev/null 2>&1 || true
}

# Set up cleanup trap
trap cleanup EXIT

# Run main validation
main "$@"