#!/bin/bash
# Final Vader test runner - mimics legacy test approach
set -euo pipefail

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

# Install vader.vim if not present
if [ ! -d /root/.vim/pack/vader/start/vader.vim ]; then
    mkdir -p /root/.vim/pack/vader/start
    git clone --depth 1 https://github.com/junegunn/vader.vim.git /root/.vim/pack/vader/start/vader.vim >/dev/null 2>&1 || true
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
echo "=== Starting Vader test: PLACEHOLDER_TEST_FILE ==="
timeout 45 $VIM_BINARY \
    --not-a-term \
    --clean \
    -i NONE \
    -u /root/.vimrc \
    -c "Vader! PLACEHOLDER_TEST_FILE" \
    +q \
    < /dev/null > "$VIM_OUTPUT_FILE" 2>&1

EXIT_CODE=$?
echo "=== Vim exit code: $EXIT_CODE ==="

# Show all output for debugging
echo "=== Full Vader output ==="
cat "$VIM_OUTPUT_FILE" 2>/dev/null || echo "No output file generated"
echo "=== End output ==="

# Check the output for success
if grep -q "Success/Total.*[1-9]" "$VIM_OUTPUT_FILE" 2>/dev/null && ! grep -q "FAILED" "$VIM_OUTPUT_FILE" 2>/dev/null; then
    echo "SUCCESS: Test passed"
    exit 0
else
    echo "ERROR: Test failed"
    echo "=== Debug info ==="
    echo "Exit code: $EXIT_CODE"
    echo "Output file size: $(wc -l < "$VIM_OUTPUT_FILE" 2>/dev/null || echo 0) lines"
    exit 1
fi
EOFSCRIPT
    )
    
    # Replace placeholder with actual test file
    TEST_SCRIPT="${TEST_SCRIPT//PLACEHOLDER_TEST_FILE/$test_file}"
    
    # Run test in container and capture full output
    OUTPUT=$(echo "$TEST_SCRIPT" | docker compose run --rm -i python-mode-tests bash 2>&1)
    
    if echo "$OUTPUT" | grep -q "SUCCESS: Test passed"; then
        log_success "Test passed: $test_name"
        PASSED_TESTS+=("$test_name")
    else
        log_error "Test failed: $test_name"
        echo "--- Error Details for $test_name ---"
        echo "$OUTPUT" | tail -30
        echo "--- End Error Details ---"
        FAILED_TESTS+=("$test_name")
    fi
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
