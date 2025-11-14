#!/bin/bash
# Generate PR summary from test results JSON files
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

ARTIFACTS_DIR="${1:-test-results-artifacts}"
OUTPUT_FILE="${2:-pr-summary.md}"

echo "Generating PR summary from test results..."
echo "Artifacts directory: $ARTIFACTS_DIR"

# Initialize summary variables
TOTAL_PYTHON_VERSIONS=0
TOTAL_TESTS=0
TOTAL_PASSED=0
TOTAL_FAILED=0
TOTAL_ASSERTIONS=0
PASSED_ASSERTIONS=0
ALL_PASSED=true
FAILED_VERSIONS=()
PASSED_VERSIONS=()

# Start markdown output
cat > "$OUTPUT_FILE" << 'EOF'
## 🧪 Test Results Summary

This comment will be updated automatically as tests complete.

EOF

# Check if artifacts directory exists and has content
if [ ! -d "$ARTIFACTS_DIR" ] || [ -z "$(ls -A "$ARTIFACTS_DIR" 2>/dev/null)" ]; then
    echo "⚠️ No test artifacts found in $ARTIFACTS_DIR" >> "$OUTPUT_FILE"
    echo "Tests may still be running or failed to upload artifacts." >> "$OUTPUT_FILE"
    exit 0
fi

# Process each Python version's test results
# Handle both direct artifact structure and nested structure
for artifact_dir in "$ARTIFACTS_DIR"/*/; do
    if [ ! -d "$artifact_dir" ]; then
        continue
    fi
    
    # Extract Python version from directory name (e.g., "test-results-3.10" -> "3.10")
    dir_name=$(basename "$artifact_dir")
    python_version="${dir_name#test-results-}"
    
    # Look for test-results.json in the artifact directory
    results_file="$artifact_dir/test-results.json"
    
    if [ ! -f "$results_file" ]; then
        echo "⚠️ Warning: test-results.json not found for Python $python_version (looked in: $results_file)" >> "$OUTPUT_FILE"
        echo "Available files in $artifact_dir:" >> "$OUTPUT_FILE"
        ls -la "$artifact_dir" >> "$OUTPUT_FILE" 2>&1 || true
        continue
    fi
    
    # Parse JSON (using jq if available, otherwise use basic parsing)
    if command -v jq &> /dev/null; then
        total_tests=$(jq -r '.total_tests // 0' "$results_file")
        passed_tests=$(jq -r '.passed_tests // 0' "$results_file")
        failed_tests=$(jq -r '.failed_tests // 0' "$results_file")
        total_assertions=$(jq -r '.total_assertions // 0' "$results_file")
        passed_assertions=$(jq -r '.passed_assertions // 0' "$results_file")
        python_ver=$(jq -r '.python_version // "unknown"' "$results_file")
        vim_ver=$(jq -r '.vim_version // "unknown"' "$results_file")
        
        # Get failed test names
        failed_test_names=$(jq -r '.results.failed[]?' "$results_file" 2>/dev/null | tr '\n' ',' | sed 's/,$//' || echo "")
    else
        # Fallback: basic parsing without jq
        total_tests=$(grep -o '"total_tests":[0-9]*' "$results_file" | grep -o '[0-9]*' || echo "0")
        passed_tests=$(grep -o '"passed_tests":[0-9]*' "$results_file" | grep -o '[0-9]*' || echo "0")
        failed_tests=$(grep -o '"failed_tests":[0-9]*' "$results_file" | grep -o '[0-9]*' || echo "0")
        total_assertions=$(grep -o '"total_assertions":[0-9]*' "$results_file" | grep -o '[0-9]*' || echo "0")
        passed_assertions=$(grep -o '"passed_assertions":[0-9]*' "$results_file" | grep -o '[0-9]*' || echo "0")
        python_ver="Python $python_version"
        vim_ver="unknown"
        failed_test_names=""
    fi
    
    TOTAL_PYTHON_VERSIONS=$((TOTAL_PYTHON_VERSIONS + 1))
    TOTAL_TESTS=$((TOTAL_TESTS + total_tests))
    TOTAL_PASSED=$((TOTAL_PASSED + passed_tests))
    TOTAL_FAILED=$((TOTAL_FAILED + failed_tests))
    TOTAL_ASSERTIONS=$((TOTAL_ASSERTIONS + total_assertions))
    PASSED_ASSERTIONS=$((PASSED_ASSERTIONS + passed_assertions))
    
    # Determine status
    if [ "$failed_tests" -gt 0 ]; then
        ALL_PASSED=false
        FAILED_VERSIONS+=("$python_version")
        status_icon="❌"
        status_text="FAILED"
    else
        PASSED_VERSIONS+=("$python_version")
        status_icon="✅"
        status_text="PASSED"
    fi
    
    # Add version summary to markdown
    cat >> "$OUTPUT_FILE" << EOF

### Python $python_version $status_icon

- **Status**: $status_text
- **Python Version**: $python_ver
- **Vim Version**: $vim_ver
- **Tests**: $passed_tests/$total_tests passed
- **Assertions**: $passed_assertions/$total_assertions passed

EOF
    
    # Add failed tests if any
    if [ "$failed_tests" -gt 0 ] && [ -n "$failed_test_names" ]; then
        echo "**Failed tests:**" >> "$OUTPUT_FILE"
        if command -v jq &> /dev/null; then
            jq -r '.results.failed[]?' "$results_file" 2>/dev/null | while read -r test_name; do
                echo "- \`$test_name\`" >> "$OUTPUT_FILE"
            done || true
        else
            # Basic parsing fallback
            echo "- See test logs for details" >> "$OUTPUT_FILE"
        fi
        echo "" >> "$OUTPUT_FILE"
    fi
done

# Add overall summary
cat >> "$OUTPUT_FILE" << EOF

---

### 📊 Overall Summary

- **Python Versions Tested**: $TOTAL_PYTHON_VERSIONS
- **Total Tests**: $TOTAL_TESTS
- **Passed**: $TOTAL_PASSED
- **Failed**: $TOTAL_FAILED
- **Total Assertions**: $TOTAL_ASSERTIONS
- **Passed Assertions**: $PASSED_ASSERTIONS

EOF

# Add status summary
if [ "$ALL_PASSED" = true ]; then
    cat >> "$OUTPUT_FILE" << EOF
**🎉 All tests passed across all Python versions!**

EOF
else
    cat >> "$OUTPUT_FILE" << EOF
**⚠️ Some tests failed:**

EOF
    for version in "${FAILED_VERSIONS[@]}"; do
        echo "- Python $version" >> "$OUTPUT_FILE"
    done
    echo "" >> "$OUTPUT_FILE"
fi

# Add footer
cat >> "$OUTPUT_FILE" << EOF

---
*Generated automatically by CI/CD workflow*
EOF

echo "Summary generated: $OUTPUT_FILE"
cat "$OUTPUT_FILE"

# Exit with error if any tests failed
if [ "$ALL_PASSED" = false ]; then
    exit 1
fi

exit 0

