#!/bin/bash
# Migration validation script for Ruff integration
# This script verifies that the Ruff migration is properly configured

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track validation results
ERRORS=0
WARNINGS=0

echo "Validating Ruff migration setup..."
echo ""

# Check 1: Verify Ruff is installed
echo -n "Checking Ruff installation... "
if command -v ruff &> /dev/null; then
    RUFF_VERSION=$(ruff --version 2>&1 | head -n1)
    echo -e "${GREEN}✓${NC} Found: $RUFF_VERSION"
else
    echo -e "${RED}✗${NC} Ruff not found"
    echo "  Install with: pip install ruff"
    ERRORS=$((ERRORS + 1))
fi

# Check 2: Verify ruff_integration.py exists
echo -n "Checking ruff_integration.py... "
if [ -f "$PROJECT_ROOT/pymode/ruff_integration.py" ]; then
    echo -e "${GREEN}✓${NC} Found"
else
    echo -e "${RED}✗${NC} Not found"
    ERRORS=$((ERRORS + 1))
fi

# Check 3: Verify lint.py uses ruff_integration
echo -n "Checking lint.py integration... "
if grep -q "ruff_integration" "$PROJECT_ROOT/pymode/lint.py" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Integrated"
else
    echo -e "${YELLOW}⚠${NC} May not be using ruff_integration"
    WARNINGS=$((WARNINGS + 1))
fi

# Check 4: Verify submodules are removed
echo -n "Checking removed submodules... "
REMOVED_SUBMODULES=("pyflakes" "pycodestyle" "mccabe" "pylint" "pydocstyle" "pylama" "autopep8" "snowball_py")
MISSING_SUBMODULES=0
for submodule in "${REMOVED_SUBMODULES[@]}"; do
    if [ -d "$PROJECT_ROOT/submodules/$submodule" ]; then
        echo -e "${YELLOW}⚠${NC} Submodule still exists: $submodule"
        MISSING_SUBMODULES=$((MISSING_SUBMODULES + 1))
    fi
done
if [ $MISSING_SUBMODULES -eq 0 ]; then
    echo -e "${GREEN}✓${NC} All removed submodules cleaned up"
else
    WARNINGS=$((WARNINGS + MISSING_SUBMODULES))
fi

# Check 5: Verify required submodules exist
echo -n "Checking required submodules... "
REQUIRED_SUBMODULES=("rope" "tomli" "pytoolconfig")
MISSING_REQUIRED=0
for submodule in "${REQUIRED_SUBMODULES[@]}"; do
    if [ ! -d "$PROJECT_ROOT/submodules/$submodule" ]; then
        echo -e "${RED}✗${NC} Required submodule missing: $submodule"
        MISSING_REQUIRED=$((MISSING_REQUIRED + 1))
    fi
done
if [ $MISSING_REQUIRED -eq 0 ]; then
    echo -e "${GREEN}✓${NC} All required submodules present"
else
    ERRORS=$((ERRORS + MISSING_REQUIRED))
fi

# Check 6: Verify .gitmodules doesn't reference removed submodules
echo -n "Checking .gitmodules... "
if [ -f "$PROJECT_ROOT/.gitmodules" ]; then
    REMOVED_IN_GITMODULES=0
    for submodule in "${REMOVED_SUBMODULES[@]}"; do
        if grep -q "\[submodule.*$submodule" "$PROJECT_ROOT/.gitmodules" 2>/dev/null; then
            echo -e "${YELLOW}⚠${NC} Still referenced in .gitmodules: $submodule"
            REMOVED_IN_GITMODULES=$((REMOVED_IN_GITMODULES + 1))
        fi
    done
    if [ $REMOVED_IN_GITMODULES -eq 0 ]; then
        echo -e "${GREEN}✓${NC} Clean"
    else
        WARNINGS=$((WARNINGS + REMOVED_IN_GITMODULES))
    fi
else
    echo -e "${YELLOW}⚠${NC} .gitmodules not found (may not be a git repo)"
fi

# Check 7: Verify Dockerfile includes ruff
echo -n "Checking Dockerfile... "
if [ -f "$PROJECT_ROOT/Dockerfile" ]; then
    if grep -q "ruff" "$PROJECT_ROOT/Dockerfile" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} Ruff included"
    else
        echo -e "${YELLOW}⚠${NC} Ruff not found in Dockerfile"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo -e "${YELLOW}⚠${NC} Dockerfile not found"
fi

# Check 8: Verify tests exist
echo -n "Checking Ruff tests... "
if [ -f "$PROJECT_ROOT/tests/vader/ruff_integration.vader" ]; then
    echo -e "${GREEN}✓${NC} Found"
else
    echo -e "${YELLOW}⚠${NC} Not found"
    WARNINGS=$((WARNINGS + 1))
fi

# Check 9: Verify documentation exists
echo -n "Checking documentation... "
DOCS_FOUND=0
if [ -f "$PROJECT_ROOT/MIGRATION_GUIDE.md" ]; then
    DOCS_FOUND=$((DOCS_FOUND + 1))
fi
if [ -f "$PROJECT_ROOT/RUFF_CONFIGURATION_MAPPING.md" ]; then
    DOCS_FOUND=$((DOCS_FOUND + 1))
fi
if [ $DOCS_FOUND -eq 2 ]; then
    echo -e "${GREEN}✓${NC} Complete"
elif [ $DOCS_FOUND -eq 1 ]; then
    echo -e "${YELLOW}⚠${NC} Partial"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${YELLOW}⚠${NC} Missing"
    WARNINGS=$((WARNINGS + 1))
fi

# Check 10: Test Ruff execution (if available)
if command -v ruff &> /dev/null; then
    echo -n "Testing Ruff execution... "
    TEST_FILE=$(mktemp)
    echo "print('test')" > "$TEST_FILE"
    if ruff check "$TEST_FILE" &> /dev/null; then
        echo -e "${GREEN}✓${NC} Working"
        rm -f "$TEST_FILE"
    else
        echo -e "${YELLOW}⚠${NC} Execution test failed"
        WARNINGS=$((WARNINGS + 1))
        rm -f "$TEST_FILE"
    fi
fi

# Summary
echo ""
echo "=========================================="
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ Migration validation passed${NC}"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ Migration validation passed with warnings ($WARNINGS)${NC}"
    exit 0
else
    echo -e "${RED}✗ Migration validation failed ($ERRORS errors, $WARNINGS warnings)${NC}"
    exit 1
fi

