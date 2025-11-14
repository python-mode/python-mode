#!/bin/bash
# Test runner - runs Vader test suite
set -euo pipefail

# Cleanup function to remove temporary files on exit
cleanup() {
    # Remove any leftover temporary test scripts
    rm -f .tmp_run_test_*.sh
}
trap cleanup EXIT INT TERM

echo "⚡ Running Vader Test Suite (Final)..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

# Find test files
TEST_FILES=()
if [[ -d "tests/vader" ]]; then
    mapfile -t TEST_FILES < <(find tests/vader -name "*.vader" -type f | sort)
fi

if [[ ${#TEST_FILES[@]} -eq 0 ]]; then
    log_error "No Vader test files found"
    exit 1
fi

log_info "Found ${#TEST_FILES[@]} test file(s)"

# Log environment information for debugging
log_info "Environment:"
log_info "  Docker: $(docker --version 2>&1 || echo 'not available')"
log_info "  Docker Compose: $(docker compose version 2>&1 || echo 'not available')"
log_info "  Working directory: $(pwd)"
log_info "  CI environment: ${CI:-false}"
log_info "  GITHUB_ACTIONS: ${GITHUB_ACTIONS:-false}"
log_info "  PYTHON_VERSION: ${PYTHON_VERSION:-not set}"

# Check if docker compose is available
if ! command -v docker &> /dev/null; then
    log_error "Docker is not available"
    exit 1
fi

if ! docker compose version &> /dev/null; then
    log_error "Docker Compose is not available"
    exit 1
fi

# Ensure docker compose file exists
if [ ! -f "docker-compose.yml" ]; then
    log_error "docker-compose.yml not found in current directory"
    exit 1
fi

# Verify docker compose can see the service
if ! docker compose config --services | grep -q "python-mode-tests"; then
    log_error "python-mode-tests service not found in docker-compose.yml"
    log_info "Available services: $(docker compose config --services 2>&1 || echo 'failed to get services')"
    exit 1
fi

# Run tests using docker compose
FAILED_TESTS=()
PASSED_TESTS=()

for test_file in "${TEST_FILES[@]}"; do
    test_name=$(basename "$test_file" .vader)
    log_info "Running test: $test_name"
    
    # Create a test script that closely follows the legacy test approach
    TEST_SCRIPT=$(cat <<'EOFSCRIPT'
#!/bin/bash
set -euo pipefail
cd /workspace/python-mode

# Ensure vader.vim is available (should be installed in Dockerfile, but check anyway)
if [ ! -d /root/.vim/pack/vader/start/vader.vim ]; then
    mkdir -p /root/.vim/pack/vader/start
    git clone --depth 1 https://github.com/junegunn/vader.vim.git /root/.vim/pack/vader/start/vader.vim 2>&1 || {
        echo "ERROR: Failed to install Vader.vim"
        exit 1
    }
fi

# Set up environment variables similar to legacy tests
export VIM_BINARY=${VIM_BINARY:-vim}
export VIM_TEST_VIMRC="tests/utils/vimrc"
export VIM_OUTPUT_FILE="/tmp/vader_output.txt"
export VIM_DISPOSABLE_PYFILE="/tmp/test_sample.py"

# Create a sample Python file for testing
cat > "$VIM_DISPOSABLE_PYFILE" << 'EOFPY'
def hello():
    print("Hello, World!")
    return True
EOFPY

# Run the Vader test with minimal setup and verbose output
# Use absolute path for test file
TEST_FILE_PATH="/workspace/python-mode/PLACEHOLDER_TEST_FILE"
if [ ! -f "$TEST_FILE_PATH" ]; then
    echo "ERROR: Test file not found: $TEST_FILE_PATH"
    exit 1
fi

echo "=== Starting Vader test: $TEST_FILE_PATH ==="
echo "=== Vim binary: $VIM_BINARY ==="
echo "=== Vimrc: $VIM_TEST_VIMRC ==="
# Verify vim is available
if ! command -v "$VIM_BINARY" &> /dev/null; then
    echo "ERROR: Vim binary not found: $VIM_BINARY"
    exit 1
fi

# Use -es (ex mode, silent) for better output handling as Vader recommends
# Add explicit error handling and ensure vim exits
timeout 60 $VIM_BINARY \
    --not-a-term \
    -es \
    -i NONE \
    -u /root/.vimrc \
    -c "Vader! $TEST_FILE_PATH" \
    -c "qa!" \
    < /dev/null > "$VIM_OUTPUT_FILE" 2>&1

EXIT_CODE=$?
echo "=== Vim exit code: $EXIT_CODE ==="

# Show all output for debugging
echo "=== Full Vader output ==="
cat "$VIM_OUTPUT_FILE" 2>/dev/null || echo "No output file generated"
echo "=== End output ==="

# Check the output for success - Vader outputs various success patterns
# Look for patterns like "Success/Total: X/Y" or "X/Y tests passed" or just check for no failures
if grep -qiE "(Success/Total|tests? passed|all tests? passed)" "$VIM_OUTPUT_FILE" 2>/dev/null; then
    # Check if there are any failures mentioned
    if grep -qiE "(FAILED|failed|error)" "$VIM_OUTPUT_FILE" 2>/dev/null && ! grep -qiE "(Success/Total.*[1-9]|tests? passed)" "$VIM_OUTPUT_FILE" 2>/dev/null; then
        echo "ERROR: Test failed - failures detected in output"
        exit 1
    else
        echo "SUCCESS: Test passed"
        exit 0
    fi
elif [ "$EXIT_CODE" -eq 0 ] && ! grep -qiE "(FAILED|failed|error|E[0-9]+)" "$VIM_OUTPUT_FILE" 2>/dev/null; then
    # If exit code is 0 and no errors found, consider it a pass
    echo "SUCCESS: Test passed (exit code 0, no errors)"
    exit 0
else
    echo "ERROR: Test failed"
    echo "=== Debug info ==="
    echo "Exit code: $EXIT_CODE"
    echo "Output file size: $(wc -l < "$VIM_OUTPUT_FILE" 2>/dev/null || echo 0) lines"
    echo "Last 20 lines of output:"
    tail -20 "$VIM_OUTPUT_FILE" 2>/dev/null || echo "No output available"
    exit 1
fi
EOFSCRIPT
    )
    
    # Replace placeholder with actual test file
    # The template already has /workspace/python-mode/ prefix, so just use the relative path
    TEST_SCRIPT="${TEST_SCRIPT//PLACEHOLDER_TEST_FILE/$test_file}"
    
    # Run test in container and capture full output
    # Use a temporary file to capture output reliably
    TEMP_OUTPUT=$(mktemp)
    TEMP_SCRIPT=$(mktemp)
    echo "$TEST_SCRIPT" > "$TEMP_SCRIPT"
    chmod +x "$TEMP_SCRIPT"
    
    # Use a more reliable method: write script to workspace (which is mounted as volume)
    # This avoids stdin redirection issues that can cause hanging
    SCRIPT_PATH_IN_CONTAINER="/workspace/python-mode/.tmp_run_test_${test_name}.sh"
    cp "$TEMP_SCRIPT" ".tmp_run_test_${test_name}.sh"
    chmod +x ".tmp_run_test_${test_name}.sh"
    
    # Execute script in container with proper timeout and error handling
    # Use --no-TTY to prevent hanging on TTY allocation
    # Capture both stdout and stderr, and check exit code properly
    # Note: timeout returns 124 if timeout occurred, otherwise returns the command's exit code
    set +e  # Temporarily disable exit on error to capture exit code
    
    # Build docker compose command with environment variables
    # Environment variables are passed via -e flags before the service name
    DOCKER_ENV_ARGS=()
    if [ -n "${PYTHON_VERSION:-}" ]; then
        DOCKER_ENV_ARGS+=(-e "PYTHON_VERSION=${PYTHON_VERSION}")
    fi
    if [ -n "${GITHUB_ACTIONS:-}" ]; then
        DOCKER_ENV_ARGS+=(-e "GITHUB_ACTIONS=${GITHUB_ACTIONS}")
    fi
    
    log_info "Running docker compose with env: PYTHON_VERSION=${PYTHON_VERSION:-not set}, GITHUB_ACTIONS=${GITHUB_ACTIONS:-not set}"
    timeout 120 docker compose run --rm --no-TTY "${DOCKER_ENV_ARGS[@]}" python-mode-tests bash "$SCRIPT_PATH_IN_CONTAINER" > "$TEMP_OUTPUT" 2>&1
    DOCKER_EXIT_CODE=$?
    set -e  # Re-enable exit on error
    log_info "Docker command completed with exit code: $DOCKER_EXIT_CODE"
    
    OUTPUT=$(cat "$TEMP_OUTPUT" 2>/dev/null || echo "")
    
    # Cleanup temporary files
    rm -f "$TEMP_SCRIPT" ".tmp_run_test_${test_name}.sh"
    
    # Check if docker command timed out or failed
    if [ "$DOCKER_EXIT_CODE" -eq 124 ]; then
        log_error "Test timed out: $test_name (exceeded 120s timeout)"
        echo "--- Timeout Details for $test_name ---"
        echo "$OUTPUT" | tail -50
        echo "--- End Timeout Details ---"
        FAILED_TESTS+=("$test_name")
        rm -f "$TEMP_OUTPUT"
        continue
    fi
    
    # Check if docker compose command itself failed (e.g., image not found, service not available)
    if [ "$DOCKER_EXIT_CODE" -ne 0 ] && [ -z "$OUTPUT" ]; then
        log_error "Docker compose command failed for test: $test_name (exit code: $DOCKER_EXIT_CODE, no output)"
        log_info "Attempting to verify docker compose setup..."
        docker compose ps 2>&1 || true
        docker compose images 2>&1 || true
        FAILED_TESTS+=("$test_name")
        rm -f "$TEMP_OUTPUT"
        continue
    fi
    
    # Check if output is empty (potential issue)
    if [ -z "$OUTPUT" ]; then
        log_error "Test produced no output: $test_name"
        echo "--- Error: No output from test execution ---"
        echo "Docker exit code: $DOCKER_EXIT_CODE"
        FAILED_TESTS+=("$test_name")
        rm -f "$TEMP_OUTPUT"
        continue
    fi
    
    # Check for success message in output
    if echo "$OUTPUT" | grep -q "SUCCESS: Test passed"; then
        log_success "Test passed: $test_name"
        PASSED_TESTS+=("$test_name")
    else
        # Check if Vader reported success (even with some failures, if most pass we might want to continue)
        # Extract Success/Total ratio from output
        SUCCESS_LINE=$(echo "$OUTPUT" | grep -iE "Success/Total:" | tail -1)
        if [ -n "$SUCCESS_LINE" ]; then
            # Extract numbers like "Success/Total: 6/7" or "Success/Total: 1/8"
            TOTAL_TESTS=$(echo "$SUCCESS_LINE" | sed -nE 's/.*Success\/Total:[^0-9]*([0-9]+)\/([0-9]+).*/\2/p')
            PASSED_COUNT=$(echo "$SUCCESS_LINE" | sed -nE 's/.*Success\/Total:[^0-9]*([0-9]+)\/([0-9]+).*/\1/p')
            
            if [ -n "$TOTAL_TESTS" ] && [ -n "$PASSED_COUNT" ]; then
                if [ "$PASSED_COUNT" -eq "$TOTAL_TESTS" ]; then
                    log_success "Test passed: $test_name ($PASSED_COUNT/$TOTAL_TESTS)"
                    PASSED_TESTS+=("$test_name")
                else
                    log_error "Test partially failed: $test_name ($PASSED_COUNT/$TOTAL_TESTS passed)"
                    echo "--- Test Results for $test_name ---"
                    echo "$SUCCESS_LINE"
                    echo "$OUTPUT" | grep -E "\(X\)|FAILED|failed|error" | head -10
                    echo "--- End Test Results ---"
                    FAILED_TESTS+=("$test_name")
                fi
            else
                log_error "Test failed: $test_name (could not parse results)"
                echo "--- Error Details for $test_name ---"
                echo "Docker exit code: $DOCKER_EXIT_CODE"
                echo "$OUTPUT" | tail -50
                echo "--- End Error Details ---"
                FAILED_TESTS+=("$test_name")
            fi
        else
            log_error "Test failed: $test_name (no success message found)"
            echo "--- Error Details for $test_name ---"
            echo "Docker exit code: $DOCKER_EXIT_CODE"
            echo "$OUTPUT" | tail -50
            echo "--- End Error Details ---"
            FAILED_TESTS+=("$test_name")
        fi
    fi
    rm -f "$TEMP_OUTPUT"
done

# Summary
echo
log_info "Test Summary"
log_info "============"
log_info "Total tests: ${#TEST_FILES[@]}"
log_info "Passed: ${#PASSED_TESTS[@]}"
log_info "Failed: ${#FAILED_TESTS[@]}"

if [[ ${#FAILED_TESTS[@]} -gt 0 ]]; then
    echo
    log_error "Failed tests:"
    for test in "${FAILED_TESTS[@]}"; do
        echo "  ✗ $test"
    done
    exit 1
else
    echo
    log_success "All tests passed!"
    exit 0
fi

