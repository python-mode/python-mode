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

# Execute vim with vader
echo "Starting Vader test: $TEST_FILE"
exec timeout --kill-after=5s "${VIM_TEST_TIMEOUT:-60}s" \
    vim -X -N -u NONE -i NONE \
    -c "set noswapfile" \
    -c "set nobackup" \
    -c "set nowritebackup" \
    -c "set noundofile" \
    -c "set viminfo=" \
    -c "filetype plugin indent on" \
    -c "packloadall" \
    -c "Vader! $TEST_FILE"