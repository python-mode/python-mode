#!/bin/bash
set -euo pipefail

# Test isolation wrapper script
# Ensures complete isolation and cleanup for each test

# Color output for better visibility
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*" >&2
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*" >&2
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

# Set up signal handlers for cleanup
trap cleanup EXIT INT TERM

cleanup() {
    local exit_code=$?
    
    log_info "Starting cleanup process..."
    
    # Kill any remaining vim processes
    if pgrep -u testuser vim >/dev/null 2>&1; then
        log_warning "Killing remaining vim processes"
        pkill -u testuser vim 2>/dev/null || true
        sleep 1
        pkill -9 -u testuser vim 2>/dev/null || true
    fi
    
    # Clean up temporary files
    rm -rf /tmp/vim* /tmp/pymode* /tmp/vader* 2>/dev/null || true
    
    # Clear vim runtime files
    rm -rf ~/.viminfo ~/.vim/view/* ~/.vim/swap/* ~/.vim/backup/* ~/.vim/undo/* 2>/dev/null || true
    
    # Clean up any socket files
    find /tmp -name "*.sock" -user testuser -delete 2>/dev/null || true
    
    log_info "Cleanup completed"
    
    # Exit with original code if not zero, otherwise success
    if [[ $exit_code -ne 0 ]]; then
        log_error "Test failed with exit code: $exit_code"
        exit $exit_code
    fi
}

# Show usage information
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS] TEST_FILE

Test isolation wrapper for python-mode Vader tests.

OPTIONS:
    --help, -h          Show this help message
    --timeout SECONDS   Set test timeout (default: 60)
    --verbose, -v       Enable verbose output
    --debug             Enable debug mode with detailed logging
    --dry-run           Show what would be executed without running

EXAMPLES:
    $0 tests/vader/autopep8.vader
    $0 --timeout 120 --verbose tests/vader/folding.vader
    $0 --debug tests/vader/lint.vader

ENVIRONMENT VARIABLES:
    VIM_TEST_TIMEOUT    Test timeout in seconds (default: 60)
    VIM_TEST_VERBOSE    Enable verbose output (1/0)
    VIM_TEST_DEBUG      Enable debug mode (1/0)
EOF
}

# Parse command line arguments
TIMEOUT="${VIM_TEST_TIMEOUT:-60}"
VERBOSE="${VIM_TEST_VERBOSE:-0}"
DEBUG="${VIM_TEST_DEBUG:-0}"
DRY_RUN=0
TEST_FILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_usage
            exit 0
            ;;
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        --verbose|-v)
            VERBOSE=1
            shift
            ;;
        --debug)
            DEBUG=1
            VERBOSE=1
            shift
            ;;
        --dry-run)
            DRY_RUN=1
            shift
            ;;
        -*)
            log_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
        *)
            if [[ -z "$TEST_FILE" ]]; then
                TEST_FILE="$1"
            else
                log_error "Multiple test files specified"
                exit 1
            fi
            shift
            ;;
    esac
done

# Validate arguments
if [[ -z "$TEST_FILE" ]]; then
    log_error "No test file specified"
    show_usage
    exit 1
fi

if [[ ! -f "$TEST_FILE" ]]; then
    log_error "Test file not found: $TEST_FILE"
    exit 1
fi

# Validate timeout
if ! [[ "$TIMEOUT" =~ ^[0-9]+$ ]] || [[ "$TIMEOUT" -lt 1 ]]; then
    log_error "Invalid timeout value: $TIMEOUT"
    exit 1
fi

# Configure environment
export HOME=/home/testuser
export TERM=dumb
export VIM_TEST_MODE=1
export VADER_OUTPUT_FILE=/tmp/vader_output

# Disable all vim user configuration
export VIMINIT='set nocp | set rtp=/opt/vader.vim,/opt/python-mode,$VIMRUNTIME'
export MYVIMRC=/dev/null

# Python configuration
export PYTHONDONTWRITEBYTECODE=1
export PYTHONUNBUFFERED=1

# Create isolated temporary directory
TEST_TMP_DIR="/tmp/vim-test-$$"
mkdir -p "$TEST_TMP_DIR"
export TMPDIR="$TEST_TMP_DIR"

log_info "Starting test isolation for: $(basename "$TEST_FILE")"
log_info "Timeout: ${TIMEOUT}s, Verbose: $VERBOSE, Debug: $DEBUG"

if [[ "$VERBOSE" == "1" ]]; then
    log_info "Environment setup:"
    log_info "  HOME: $HOME"
    log_info "  TERM: $TERM"
    log_info "  TMPDIR: $TMPDIR"
    log_info "  VIM_TEST_MODE: $VIM_TEST_MODE"
fi

# Prepare vim command
VIM_CMD=(
    timeout --kill-after=5s "${TIMEOUT}s"
    vim
    -X          # No X11 connection
    -N          # Non-compatible mode
    -u NONE     # No user vimrc
    -i NONE     # No viminfo
    -n          # No swap file
    --not-a-term # Prevent terminal issues
)

# Combine all vim commands into a single -c argument to avoid "too many" error
VIM_COMMANDS="set noswapfile | set nobackup | set nowritebackup | set noundofile | set viminfo= | set nomore | set noconfirm | set shortmess=aoOtTIcFW | set belloff=all | set visualbell t_vb= | set cmdheight=20 | set report=999999 | set timeoutlen=100 | set ttimeoutlen=10 | set updatetime=100 | filetype plugin indent on | packloadall! | Vader! $TEST_FILE"

VIM_SETTINGS=(
    -c "$VIM_COMMANDS"
)

# Combine all vim arguments
FULL_VIM_CMD=("${VIM_CMD[@]}" "${VIM_SETTINGS[@]}")

if [[ "$DEBUG" == "1" ]]; then
    log_info "Full vim command:"
    printf '%s\n' "${FULL_VIM_CMD[@]}" | sed 's/^/  /'
fi

if [[ "$DRY_RUN" == "1" ]]; then
    log_info "DRY RUN - Would execute:"
    printf '%s ' "${FULL_VIM_CMD[@]}"
    echo
    exit 0
fi

# Execute the test
log_info "Executing test: $(basename "$TEST_FILE")"

# Capture start time
START_TIME=$(date +%s)

# Run vim with comprehensive error handling
if [[ "$VERBOSE" == "1" ]]; then
    "${FULL_VIM_CMD[@]}" 2>&1
    EXIT_CODE=$?
else
    "${FULL_VIM_CMD[@]}" >/dev/null 2>&1
    EXIT_CODE=$?
fi

# Calculate duration
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# Check results
if [[ $EXIT_CODE -eq 0 ]]; then
    log_success "Test passed: $(basename "$TEST_FILE") (${DURATION}s)"
elif [[ $EXIT_CODE -eq 124 ]]; then
    log_error "Test timed out: $(basename "$TEST_FILE") (${TIMEOUT}s)"
elif [[ $EXIT_CODE -eq 137 ]]; then
    log_error "Test killed: $(basename "$TEST_FILE") (${DURATION}s)"
else
    log_error "Test failed: $(basename "$TEST_FILE") (exit code: $EXIT_CODE, ${DURATION}s)"
fi

# Show vader output if available and verbose mode
if [[ "$VERBOSE" == "1" && -f "$VADER_OUTPUT_FILE" ]]; then
    log_info "Vader output:"
    cat "$VADER_OUTPUT_FILE" | sed 's/^/  /'
fi

# Final cleanup will be handled by trap
exit $EXIT_CODE