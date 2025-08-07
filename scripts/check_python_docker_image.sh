#!/bin/bash
# Script to check if a Python Docker image exists and provide fallback

PYTHON_VERSION="${1:-3.11}"

# In CI environment, use simpler logic without pulling
if [ -n "$GITHUB_ACTIONS" ]; then
    # For Python 3.13 in CI, use explicit version
    if [[ "$PYTHON_VERSION" == "3.13" ]]; then
        echo "3.13.0"
    else
        echo "$PYTHON_VERSION"
    fi
    exit 0
fi

# Function to check if Docker image exists (for local development)
check_docker_image() {
    local image="$1"
    local version="$2"
    # Try to inspect the image without pulling
    if docker image inspect "$image" >/dev/null 2>&1; then
        echo "$version"
        return 0
    fi
    # Try pulling if not found locally
    if docker pull "$image" --quiet 2>/dev/null; then
        echo "$version"
        return 0
    fi
    return 1
}

# For Python 3.13, try specific versions
if [[ "$PYTHON_VERSION" == "3.13" ]]; then
    # Try different Python 3.13 versions
    for version in "3.13.0" "3.13" "3.13-rc" "3.13.0rc3"; do
        if check_docker_image "python:${version}-slim" "${version}"; then
            exit 0
        fi
    done
    # If no 3.13 version works, fall back to 3.12
    echo "Warning: Python 3.13 image not found, using 3.12 instead" >&2
    echo "3.12"
else
    # For other versions, return as-is
    echo "$PYTHON_VERSION"
fi