#!/bin/bash

# Script to run python-mode tests with all Python versions
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Cleanup function to remove root-owned files created by Docker container
# This function ensures cleanup only happens within the git repository root
cleanup_root_files() {
    local provided_path="${1:-$(pwd)}"
    
    # Find git root directory - this ensures we only operate within the project
    local git_root
    if ! git_root=$(cd "$provided_path" && git rev-parse --show-toplevel 2>/dev/null); then
        echo -e "${YELLOW}Warning: Not in a git repository, skipping cleanup${NC}" >&2
        return 0
    fi
    
    # Normalize paths for comparison
    git_root=$(cd "$git_root" && pwd)
    local normalized_path=$(cd "$provided_path" && pwd)
    
    # Safety check: ensure the provided path is within git root
    if [[ "$normalized_path" != "$git_root"* ]]; then
        echo -e "${RED}Error: Path '$normalized_path' is outside git root '$git_root', aborting cleanup${NC}" >&2
        return 1
    fi
    
    # Use git root as the base for cleanup operations
    local project_root="$git_root"
    echo -e "${YELLOW}Cleaning up files created by Docker container in: $project_root${NC}"
    
    # Find and remove root-owned files/directories that shouldn't persist
    # Use sudo if available, otherwise try without (may fail silently)
    if command -v sudo &> /dev/null; then
        # Remove Python cache files (only within git root)
        sudo find "$project_root" -type d -name "__pycache__" -user root -exec rm -rf {} + 2>/dev/null || true
        sudo find "$project_root" -type f \( -name "*.pyc" -o -name "*.pyo" \) -user root -delete 2>/dev/null || true
        
        # Remove temporary test scripts (only within git root)
        sudo find "$project_root" -type f -name ".tmp_run_test_*.sh" -user root -delete 2>/dev/null || true
        
        # Remove test artifacts (only within git root)
        sudo rm -rf "$project_root/test-logs" "$project_root/results" 2>/dev/null || true
        sudo rm -f "$project_root/test-results.json" "$project_root/coverage.xml" 2>/dev/null || true
        
        # Remove Vim swap files (only within git root)
        sudo find "$project_root" -type f \( -name "*.swp" -o -name "*.swo" -o -name ".*.swp" -o -name ".*.swo" \) -user root -delete 2>/dev/null || true
    else
        # Without sudo, try to remove files we can access (only within git root)
        find "$project_root" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
        find "$project_root" -type f \( -name "*.pyc" -o -name "*.pyo" -o -name ".tmp_run_test_*.sh" -o -name "*.swp" -o -name "*.swo" \) -delete 2>/dev/null || true
        rm -rf "$project_root/test-logs" "$project_root/results" 2>/dev/null || true
        rm -f "$project_root/test-results.json" "$project_root/coverage.xml" 2>/dev/null || true
    fi
}

# Mapping of major.minor to full version (same as run-tests-docker.sh in user folder)
declare -A PYTHON_VERSIONS
PYTHON_VERSIONS["3.10"]="3.10.13"
PYTHON_VERSIONS["3.11"]="3.11.9"
PYTHON_VERSIONS["3.12"]="3.12.4"
PYTHON_VERSIONS["3.13"]="3.13.0"

echo -e "${YELLOW}Running python-mode tests with all Python versions...${NC}"
echo ""

# Build the Docker image once
echo -e "${YELLOW}Building python-mode test environment...${NC}"
docker compose build -q python-mode-tests
echo ""

# Track overall results
OVERALL_SUCCESS=true
FAILED_VERSIONS=()

# Test each Python version
for short_version in "${!PYTHON_VERSIONS[@]}"; do
    full_version="${PYTHON_VERSIONS[$short_version]}"
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Testing with Python $short_version ($full_version)${NC}"
    echo -e "${BLUE}========================================${NC}"
    
    if docker compose run --rm -e PYTHON_VERSION="$full_version" python-mode-tests; then
        echo -e "${GREEN}✓ Tests passed with Python $short_version${NC}"
    else
        echo -e "${RED}✗ Tests failed with Python $short_version${NC}"
        OVERALL_SUCCESS=false
        FAILED_VERSIONS+=("$short_version")
    fi
    echo ""
done

# Cleanup root-owned files after all tests
cleanup_root_files "$(pwd)"

# Summary
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}TEST SUMMARY${NC}"
echo -e "${YELLOW}========================================${NC}"

if [ "$OVERALL_SUCCESS" = true ]; then
    echo -e "${GREEN}✓ All tests passed for all Python versions!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed for the following Python versions:${NC}"
    for version in "${FAILED_VERSIONS[@]}"; do
        echo -e "${RED}  - Python $version (${PYTHON_VERSIONS[$version]})${NC}"
    done
    echo ""
    echo -e "${YELLOW}To run tests for a specific version:${NC}"
    echo -e "${BLUE}  ./scripts/user/run-tests-docker.sh <major.minor>${NC}"
    echo -e "${BLUE}  Example: ./scripts/user/run-tests-docker.sh 3.11${NC}"
    exit 1
fi 