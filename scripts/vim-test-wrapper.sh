#!/bin/bash
set -euo pipefail

# Vim test wrapper script
# Provides additional safety measures for vim execution in tests

# Enhanced vim wrapper that handles various edge cases
exec_vim_safe() {
    local args=()
    local has_not_a_term=false
    
    # Process arguments to handle --not-a-term flag
    for arg in "$@"; do
        case "$arg" in
            --not-a-term)
                has_not_a_term=true
                args+=("-X")  # Use -X instead of --not-a-term for better compatibility
                ;;
            *)
                args+=("$arg")
                ;;
        esac
    done
    
    # Add additional safety flags if not already present
    local has_x_flag=false
    local has_n_flag=false
    local has_u_flag=false
    
    for arg in "${args[@]}"; do
        case "$arg" in
            -X) has_x_flag=true ;;
            -N) has_n_flag=true ;;
            -u) has_u_flag=true ;;
        esac
    done
    
    # Add missing safety flags
    if [[ "$has_x_flag" == "false" ]]; then
        args=("-X" "${args[@]}")
    fi
    
    if [[ "$has_n_flag" == "false" ]]; then
        args=("-N" "${args[@]}")
    fi
    
    # Set environment for safer vim execution
    export TERM=dumb
    export DISPLAY=""
    
    # Execute vim with enhanced arguments
    exec vim "${args[@]}"
}

# Check if we're being called as a vim replacement
if [[ "${0##*/}" == "vim" ]] || [[ "${0##*/}" == "vim-test-wrapper.sh" ]]; then
    exec_vim_safe "$@"
else
    # If called directly, show usage
    cat << 'EOF'
Vim Test Wrapper

This script provides a safer vim execution environment for testing.

Usage:
  vim-test-wrapper.sh [vim-options] [files...]
  
Or create a symlink named 'vim' to use as a drop-in replacement:
  ln -s /path/to/vim-test-wrapper.sh /usr/local/bin/vim

Features:
  - Converts --not-a-term to -X for better compatibility
  - Adds safety flags automatically (-X, -N)
  - Sets safe environment variables
  - Prevents X11 connection attempts
EOF
fi