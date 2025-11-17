#!/bin/bash
# Direct CI Test Runner - Runs Vader tests without Docker
# This script is designed to run in GitHub Actions CI environment

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
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

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${PROJECT_ROOT}"

log_info "Project root: ${PROJECT_ROOT}"
log_info "Python version: $(python3 --version 2>&1 || echo 'not available')"
log_info "Vim version: $(vim --version | head -1 || echo 'not available')"

# Check prerequisites
if ! command -v vim &> /dev/null; then
    log_error "Vim is not installed"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    log_error "Python3 is not installed"
    exit 1
fi

# Set up Vim runtime paths
VIM_HOME="${HOME}/.vim"
VADER_DIR="${VIM_HOME}/pack/vader/start/vader.vim"
PYMODE_DIR="${PROJECT_ROOT}"

# Install Vader.vim if not present
if [ ! -d "${VADER_DIR}" ]; then
    log_info "Installing Vader.vim..."
    mkdir -p "$(dirname "${VADER_DIR}")"
    git clone --depth 1 https://github.com/junegunn/vader.vim.git "${VADER_DIR}" || {
        log_error "Failed to install Vader.vim"
        exit 1
    }
    log_success "Vader.vim installed"
else
    log_info "Vader.vim already installed"
fi

# Create a CI-specific vimrc
CI_VIMRC="${PROJECT_ROOT}/tests/utils/vimrc.ci"
VIM_HOME_ESC=$(echo "${VIM_HOME}" | sed 's/\//\\\//g')
PROJECT_ROOT_ESC=$(echo "${PROJECT_ROOT}" | sed 's/\//\\\//g')

cat > "${CI_VIMRC}" << EOFVIMRC
" CI-specific vimrc for direct test execution
set nocompatible
set nomore
set shortmess=at
set cmdheight=10
set backupdir=
set directory=
set undodir=
set viewdir=
set noswapfile
set paste
set shell=bash

" Enable magic for motion support (required for text object mappings)
set magic

" Enable filetype detection
filetype plugin indent on
syntax on

" Set up runtimepath for CI environment
let s:vim_home = '${VIM_HOME_ESC}'
let s:project_root = '${PROJECT_ROOT_ESC}'

" Add Vader.vim to runtimepath
execute 'set rtp+=' . s:vim_home . '/pack/vader/start/vader.vim'

" Add python-mode to runtimepath
execute 'set rtp+=' . s:project_root

" Load python-mode configuration FIRST to set g:pymode_rope = 1
" This ensures the plugin will define all rope variables when it loads
if filereadable(s:project_root . '/tests/utils/pymoderc')
    execute 'source ' . s:project_root . '/tests/utils/pymoderc'
endif

" Load python-mode plugin AFTER pymoderc so it sees rope is enabled
" and defines all rope configuration variables
runtime plugin/pymode.vim

" Ensure rope variables exist even if rope gets disabled later
" The plugin only defines these when g:pymode_rope is enabled,
" but tests expect them to exist even when rope is disabled
if !exists('g:pymode_rope_completion')
    let g:pymode_rope_completion = 1
endif
if !exists('g:pymode_rope_autoimport_import_after_complete')
    let g:pymode_rope_autoimport_import_after_complete = 0
endif
if !exists('g:pymode_rope_regenerate_on_write')
    let g:pymode_rope_regenerate_on_write = 1
endif
if !exists('g:pymode_rope_goto_definition_bind')
    let g:pymode_rope_goto_definition_bind = '<C-c>g'
endif
if !exists('g:pymode_rope_rename_bind')
    let g:pymode_rope_rename_bind = '<C-c>rr'
endif
if !exists('g:pymode_rope_extract_method_bind')
    let g:pymode_rope_extract_method_bind = '<C-c>rm'
endif
if !exists('g:pymode_rope_organize_imports_bind')
    let g:pymode_rope_organize_imports_bind = '<C-c>ro'
endif

" Note: Tests will initialize python-mode via tests/vader/setup.vim
" which is sourced in each test's "Before" block. The setup.vim may
" disable rope (g:pymode_rope = 0), but the config variables will
" still exist because they were defined above.
EOFVIMRC

log_info "Created CI vimrc at ${CI_VIMRC}"

# Find test files
TEST_FILES=()
if [[ -d "tests/vader" ]]; then
    mapfile -t TEST_FILES < <(find tests/vader -name "*.vader" -type f | sort)
fi

if [[ ${#TEST_FILES[@]} -eq 0 ]]; then
    log_error "No Vader test files found in tests/vader/"
    exit 1
fi

log_info "Found ${#TEST_FILES[@]} test file(s)"

# Run tests
FAILED_TESTS=()
PASSED_TESTS=()
TOTAL_ASSERTIONS=0
PASSED_ASSERTIONS=0

for test_file in "${TEST_FILES[@]}"; do
    test_name=$(basename "$test_file" .vader)
    log_info "Running test: ${test_name}"
    
    # Use absolute path for test file
    TEST_FILE_ABS="${PROJECT_ROOT}/${test_file}"
    
    if [ ! -f "${TEST_FILE_ABS}" ]; then
        log_error "Test file not found: ${TEST_FILE_ABS}"
        FAILED_TESTS+=("${test_name}")
        continue
    fi
    
    # Create output file for this test
    VIM_OUTPUT_FILE=$(mktemp)
    
    # Run Vader test with timeout
    # macOS doesn't have timeout by default, so use gtimeout if available, or run without timeout
    set +e  # Don't exit on error, we'll check exit code
    if command -v timeout &> /dev/null; then
        timeout 120 vim \
            --not-a-term \
            -es \
            -i NONE \
            -u "${CI_VIMRC}" \
            -c "Vader! ${TEST_FILE_ABS}" \
            -c "qa!" \
            < /dev/null > "${VIM_OUTPUT_FILE}" 2>&1
        EXIT_CODE=$?
    elif command -v gtimeout &> /dev/null; then
        # macOS with GNU coreutils installed via Homebrew
        gtimeout 120 vim \
            --not-a-term \
            -es \
            -i NONE \
            -u "${CI_VIMRC}" \
            -c "Vader! ${TEST_FILE_ABS}" \
            -c "qa!" \
            < /dev/null > "${VIM_OUTPUT_FILE}" 2>&1
        EXIT_CODE=$?
    else
        # No timeout available (macOS without GNU coreutils)
        # Run without timeout - tests should complete quickly anyway
        log_warn "timeout command not available, running without timeout"
        vim \
            --not-a-term \
            -es \
            -i NONE \
            -u "${CI_VIMRC}" \
            -c "Vader! ${TEST_FILE_ABS}" \
            -c "qa!" \
            < /dev/null > "${VIM_OUTPUT_FILE}" 2>&1
        EXIT_CODE=$?
    fi
    set -e
    
    OUTPUT=$(cat "${VIM_OUTPUT_FILE}" 2>/dev/null || echo "")
    rm -f "${VIM_OUTPUT_FILE}"
    
    # Check for timeout
    if [ "${EXIT_CODE}" -eq 124 ]; then
        log_error "Test timed out: ${test_name} (exceeded 120s timeout)"
        FAILED_TESTS+=("${test_name}")
        continue
    fi
    
    # Parse Vader output for success/failure
    if echo "${OUTPUT}" | grep -qiE "Success/Total:"; then
        # Extract success/total counts
        SUCCESS_LINE=$(echo "${OUTPUT}" | grep -iE "Success/Total:" | tail -1)
        TOTAL_TESTS=$(echo "${SUCCESS_LINE}" | sed -nE 's/.*Success\/Total:[^0-9]*([0-9]+)\/([0-9]+).*/\2/p')
        PASSED_COUNT=$(echo "${SUCCESS_LINE}" | sed -nE 's/.*Success\/Total:[^0-9]*([0-9]+)\/([0-9]+).*/\1/p')
        
        # Extract assertion counts if available
        if echo "${OUTPUT}" | grep -qiE "assertions:"; then
            ASSERT_LINE=$(echo "${OUTPUT}" | grep -iE "assertions:" | tail -1)
            ASSERT_TOTAL=$(echo "${ASSERT_LINE}" | sed -nE 's/.*assertions:[^0-9]*([0-9]+)\/([0-9]+).*/\2/p')
            ASSERT_PASSED=$(echo "${ASSERT_LINE}" | sed -nE 's/.*assertions:[^0-9]*([0-9]+)\/([0-9]+).*/\1/p')
            if [ -n "${ASSERT_TOTAL}" ] && [ -n "${ASSERT_PASSED}" ]; then
                TOTAL_ASSERTIONS=$((TOTAL_ASSERTIONS + ASSERT_TOTAL))
                PASSED_ASSERTIONS=$((PASSED_ASSERTIONS + ASSERT_PASSED))
            fi
        fi
        
        if [ -n "${TOTAL_TESTS}" ] && [ -n "${PASSED_COUNT}" ]; then
            if [ "${PASSED_COUNT}" -eq "${TOTAL_TESTS}" ]; then
                log_success "Test passed: ${test_name} (${PASSED_COUNT}/${TOTAL_TESTS})"
                PASSED_TESTS+=("${test_name}")
            else
                log_error "Test failed: ${test_name} (${PASSED_COUNT}/${TOTAL_TESTS} passed)"
                echo "--- Test Output for ${test_name} ---"
                echo "${OUTPUT}" | tail -30
                echo "--- End Output ---"
                FAILED_TESTS+=("${test_name}")
            fi
        else
            log_error "Test failed: ${test_name} (could not parse results)"
            echo "--- Test Output for ${test_name} ---"
            echo "${OUTPUT}" | tail -30
            echo "--- End Output ---"
            FAILED_TESTS+=("${test_name}")
        fi
    elif [ "${EXIT_CODE}" -eq 0 ] && ! echo "${OUTPUT}" | grep -qiE "(FAILED|failed|error|E[0-9]+)"; then
        # Exit code 0 and no errors found - consider it a pass
        log_success "Test passed: ${test_name} (exit code 0, no errors)"
        PASSED_TESTS+=("${test_name}")
    else
        log_error "Test failed: ${test_name}"
        echo "--- Test Output for ${test_name} ---"
        echo "Exit code: ${EXIT_CODE}"
        echo "${OUTPUT}" | tail -50
        echo "--- End Output ---"
        FAILED_TESTS+=("${test_name}")
    fi
done

# Generate test results JSON
RESULTS_DIR="${PROJECT_ROOT}/results"
LOGS_DIR="${PROJECT_ROOT}/test-logs"
mkdir -p "${RESULTS_DIR}" "${LOGS_DIR}"

# Function to format array as JSON array with proper escaping
format_json_array() {
    local arr=("$@")
    if [ ${#arr[@]} -eq 0 ]; then
        echo "[]"
        return
    fi
    local result="["
    local first=true
    for item in "${arr[@]}"; do
        if [ "$first" = true ]; then
            first=false
        else
            result+=","
        fi
        # Escape JSON special characters: ", \, and control characters
        local escaped=$(echo "$item" | sed 's/\\/\\\\/g' | sed 's/"/\\"/g' | sed 's/\x00//g')
        result+="\"${escaped}\""
    done
    result+="]"
    echo "$result"
}

TEST_RESULTS_JSON="${PROJECT_ROOT}/test-results.json"
PASSED_ARRAY_JSON=$(format_json_array "${PASSED_TESTS[@]}")
FAILED_ARRAY_JSON=$(format_json_array "${FAILED_TESTS[@]}")

cat > "${TEST_RESULTS_JSON}" << EOF
{
  "timestamp": $(date +%s),
  "python_version": "$(python3 --version 2>&1 | awk '{print $2}')",
  "vim_version": "$(vim --version | head -1 | awk '{print $5}')",
  "total_tests": ${#TEST_FILES[@]},
  "passed_tests": ${#PASSED_TESTS[@]},
  "failed_tests": ${#FAILED_TESTS[@]},
  "total_assertions": ${TOTAL_ASSERTIONS},
  "passed_assertions": ${PASSED_ASSERTIONS},
  "results": {
    "passed": ${PASSED_ARRAY_JSON},
    "failed": ${FAILED_ARRAY_JSON}
  }
}
EOF

# Validate JSON syntax if jq or python is available
if command -v jq &> /dev/null; then
    if ! jq empty "${TEST_RESULTS_JSON}" 2>/dev/null; then
        log_error "Generated JSON is invalid!"
        cat "${TEST_RESULTS_JSON}"
        exit 1
    fi
elif command -v python3 &> /dev/null; then
    if ! python3 -m json.tool "${TEST_RESULTS_JSON}" > /dev/null 2>&1; then
        log_error "Generated JSON is invalid!"
        cat "${TEST_RESULTS_JSON}"
        exit 1
    fi
fi

# Create summary log
SUMMARY_LOG="${LOGS_DIR}/test-summary.log"
cat > "${SUMMARY_LOG}" << EOF
Test Summary
============
Python Version: $(python3 --version 2>&1)
Vim Version: $(vim --version | head -1)
Timestamp: $(date)

Total Tests: ${#TEST_FILES[@]}
Passed: ${#PASSED_TESTS[@]}
Failed: ${#FAILED_TESTS[@]}
Total Assertions: ${TOTAL_ASSERTIONS}
Passed Assertions: ${PASSED_ASSERTIONS}

Passed Tests:
$(for test in "${PASSED_TESTS[@]}"; do echo "  ✓ ${test}"; done)

Failed Tests:
$(for test in "${FAILED_TESTS[@]}"; do echo "  ✗ ${test}"; done)
EOF

# Print summary
echo
log_info "Test Summary"
log_info "============"
log_info "Total tests: ${#TEST_FILES[@]}"
log_info "Passed: ${#PASSED_TESTS[@]}"
log_info "Failed: ${#FAILED_TESTS[@]}"
if [ ${TOTAL_ASSERTIONS} -gt 0 ]; then
    log_info "Assertions: ${PASSED_ASSERTIONS}/${TOTAL_ASSERTIONS}"
fi

if [[ ${#FAILED_TESTS[@]} -gt 0 ]]; then
    echo
    log_error "Failed tests:"
    for test in "${FAILED_TESTS[@]}"; do
        echo "  ✗ ${test}"
    done
    echo
    log_info "Test results saved to: ${TEST_RESULTS_JSON}"
    log_info "Summary log saved to: ${SUMMARY_LOG}"
    exit 1
else
    echo
    log_success "All tests passed!"
    log_info "Test results saved to: ${TEST_RESULTS_JSON}"
    log_info "Summary log saved to: ${SUMMARY_LOG}"
    exit 0
fi

