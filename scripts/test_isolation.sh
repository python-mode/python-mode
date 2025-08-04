#!/bin/bash
set -euo pipefail

# Test isolation wrapper script
# Ensures complete isolation and cleanup for each test

# Set up signal handlers
trap cleanup EXIT INT TERM

cleanup() {
    # Kill any remaining vim processes
    pkill -u testuser vim 2>/dev/null || true
    
    # Clean up temporary files
    rm -rf /tmp/vim* /tmp/pymode* 2>/dev/null || true
    
    # Clear vim info files
    rm -rf ~/.viminfo ~/.vim/view/* 2>/dev/null || true
}

# Configure environment
export HOME=/home/testuser
export TERM=dumb
export VIM_TEST_MODE=1
export VADER_OUTPUT_FILE=/tmp/vader_output

# Disable all vim user configuration
export VIMINIT='set nocp | set rtp=/opt/vader.vim,/opt/python-mode,$VIMRUNTIME'
export MYVIMRC=/dev/null

# Run the test with strict timeout
TEST_FILE="${1:-}"
if [[ -z "$TEST_FILE" ]]; then
    echo "Error: No test file specified"
    exit 1
fi

# Execute vim with vader using same flags as successful bash tests
echo "Starting Vader test: $TEST_FILE"

# Ensure we have the absolute path to the test file
if [[ "$TEST_FILE" != /* ]]; then
    # If relative path, make it absolute from /opt/python-mode
    TEST_FILE="/opt/python-mode/$TEST_FILE"
fi

exec timeout --kill-after=5s "${VIM_TEST_TIMEOUT:-60}s" \
    vim --not-a-term --clean -i NONE \
    -c "set rtp=/opt/vader.vim,/opt/python-mode,\$VIMRUNTIME" \
    -c "filetype plugin indent on" \
    -c "runtime plugin/vader.vim" \
    -c "runtime plugin/pymode.vim" \
    -c "if !exists(':Vader') | echoerr 'Vader not loaded' | cquit | endif" \
    -c "Vader $TEST_FILE"