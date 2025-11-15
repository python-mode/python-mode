#!/bin/bash
# Verify Ruff installation for python-mode
#
# This script checks if Ruff is properly installed and accessible.
# Exit code 0 means success, non-zero means failure.

set -e

echo "Checking Ruff installation for python-mode..."

# Check if ruff command exists
if ! command -v ruff &> /dev/null; then
    echo "ERROR: Ruff is not installed or not in PATH"
    echo ""
    echo "Please install Ruff using one of the following methods:"
    echo "  - pip install ruff"
    echo "  - pipx install ruff"
    echo "  - brew install ruff (macOS)"
    echo "  - cargo install ruff (from source)"
    echo ""
    echo "See https://docs.astral.sh/ruff/installation/ for more options."
    exit 1
fi

# Check ruff version
RUFF_VERSION=$(ruff --version 2>&1 | head -1)
echo "✓ Found Ruff: $RUFF_VERSION"

# Verify ruff can run check command
if ! ruff check --help &> /dev/null; then
    echo "ERROR: Ruff 'check' command is not working"
    exit 1
fi
echo "✓ Ruff 'check' command is working"

# Verify ruff can run format command
if ! ruff format --help &> /dev/null; then
    echo "ERROR: Ruff 'format' command is not working"
    exit 1
fi
echo "✓ Ruff 'format' command is working"

# Test with a simple Python file
TEMP_FILE=$(mktemp --suffix=.py)
cat > "$TEMP_FILE" << 'EOF'
def hello():
    x=1+2
    return x
EOF

# Test check command
if ruff check "$TEMP_FILE" &> /dev/null; then
    echo "✓ Ruff can check Python files"
else
    echo "WARNING: Ruff check returned non-zero (this may be expected if issues are found)"
fi

# Test format command
if ruff format --check "$TEMP_FILE" &> /dev/null; then
    echo "✓ Ruff can format Python files"
else
    echo "WARNING: Ruff format check returned non-zero (this may be expected if formatting is needed)"
fi

# Cleanup
rm -f "$TEMP_FILE"

echo ""
echo "✓ Ruff installation verified successfully!"
echo ""
echo "python-mode is ready to use Ruff for linting and formatting."

