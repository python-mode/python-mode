#! /bin/bash
# Legacy test.sh - now delegates to Vader test runner
# All bash tests have been migrated to Vader tests
# This script is kept for backward compatibility with Dockerfile

cd "$(dirname "$0")/.."

# Run Vader tests using the test runner script
if [ -f "scripts/user/run_tests.sh" ]; then
    bash scripts/user/run_tests.sh
    EXIT_CODE=$?
else
    echo "Error: Vader test runner not found at scripts/user/run_tests.sh"
    EXIT_CODE=1
fi

# Generate coverage.xml for codecov (basic structure)
# Note: Python-mode is primarily a Vim plugin, so coverage collection
# is limited. This creates a basic coverage.xml structure for CI.
PROJECT_ROOT="$(pwd)"
COVERAGE_XML="${PROJECT_ROOT}/coverage.xml"

if command -v coverage &> /dev/null; then
    # Try to generate XML report if coverage data exists
    if [ -f .coverage ]; then
        coverage xml -o "${COVERAGE_XML}" 2>/dev/null || true
    fi
fi

# Always create coverage.xml (minimal if no coverage data)
if [ ! -f "${COVERAGE_XML}" ]; then
    printf '<?xml version="1.0" ?>\n' > "${COVERAGE_XML}"
    printf '<coverage version="7.0.0">\n' >> "${COVERAGE_XML}"
    printf '    <sources>\n' >> "${COVERAGE_XML}"
    printf '        <source>%s</source>\n' "${PROJECT_ROOT}" >> "${COVERAGE_XML}"
    printf '    </sources>\n' >> "${COVERAGE_XML}"
    printf '    <packages/>\n' >> "${COVERAGE_XML}"
    printf '</coverage>\n' >> "${COVERAGE_XML}"
fi

exit ${EXIT_CODE}
# vim: set fileformat=unix filetype=sh wrap tw=0 :
