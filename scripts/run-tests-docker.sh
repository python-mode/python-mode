#!/bin/bash

# Script to run python-mode tests in Docker
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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
if docker compose run --rm python-mode-tests; then
    echo -e "${GREEN}✓ All tests passed with Python ${PYTHON_VERSION}!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed with Python ${PYTHON_VERSION}. Check the output above for details.${NC}"
    exit 1
fi
