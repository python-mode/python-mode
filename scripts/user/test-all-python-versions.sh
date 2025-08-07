#!/bin/bash

# Script to run python-mode tests with all Python versions
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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