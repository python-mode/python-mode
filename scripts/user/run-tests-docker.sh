#!/bin/bash

# Script to run python-mode tests in Docker
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

# Mapping of major.minor to full version
declare -A PYTHON_VERSIONS
PYTHON_VERSIONS["3.10"]="3.10.13"
PYTHON_VERSIONS["3.11"]="3.11.9"
PYTHON_VERSIONS["3.12"]="3.12.4"
PYTHON_VERSIONS["3.13"]="3.13.0"

show_usage() {
    echo -e "${YELLOW}Usage: $0 [major.minor]${NC}"
    echo -e "${YELLOW}Available versions:${NC}"
    for short_version in "${!PYTHON_VERSIONS[@]}"; do
        full_version="${PYTHON_VERSIONS[$short_version]}"
        echo -e "  ${BLUE}${short_version}${NC} (${full_version})"
    done
    echo ""
    echo -e "${YELLOW}Examples:${NC}"
    echo -e "  ${BLUE}$0${NC}                    # Use default Python version"
    echo -e "  ${BLUE}$0 3.10${NC}               # Test with Python 3.10.13"
    echo -e "  ${BLUE}$0 3.11${NC}               # Test with Python 3.11.9"
    echo -e "  ${BLUE}$0 3.12${NC}               # Test with Python 3.12.4"
    echo -e "  ${BLUE}$0 3.13${NC}               # Test with Python 3.13.0"
}

PYTHON_VERSION_SHORT="3.13"
PYTHON_VERSION=""

if [ $# -eq 1 ]; then
    PYTHON_VERSION_SHORT=$1

    # Check if the version is valid
    valid_version=false
    for short_version in "${!PYTHON_VERSIONS[@]}"; do
        if [ "${PYTHON_VERSION_SHORT}" = "${short_version}" ]; then
            valid_version=true
            PYTHON_VERSION="${PYTHON_VERSIONS[$short_version]}"
            break
        fi
    done

    if [ "${valid_version}" = false ]; then
        echo -e "${RED}Error: Invalid Python version '${PYTHON_VERSION_SHORT}'${NC}"
        show_usage
        exit 1
    fi
else
    # Use default version
    PYTHON_VERSION="${PYTHON_VERSIONS[$PYTHON_VERSION_SHORT]}"
fi

echo -e "${YELLOW}Building python-mode test environment...${NC}"

DOCKER_BUILD_ARGS=(
    --build-arg PYTHON_VERSION="${PYTHON_VERSION}"
)

# Build the Docker image
docker compose build -q ${DOCKER_BUILD_ARGS[@]} python-mode-tests

echo -e "${YELLOW}Running python-mode tests with Python ${PYTHON_VERSION}...${NC}"
# Run the tests with specific Python version
TEST_EXIT_CODE=0
if docker compose run --rm python-mode-tests; then
    echo -e "${GREEN}✓ All tests passed with Python ${PYTHON_VERSION}!${NC}"
else
    echo -e "${RED}✗ Some tests failed with Python ${PYTHON_VERSION}. Check the output above for details.${NC}"
    TEST_EXIT_CODE=1
fi

# Always cleanup root-owned files after Docker execution
cleanup_root_files "$(pwd)"

exit $TEST_EXIT_CODE
