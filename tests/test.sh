#! /bin/bash
# We don't want to exit on the first error that appears
set +e

# Check before starting.
which vim 1>/dev/null 2>/dev/null

cd "$(dirname "$0")"

# Source common variables.
source ./test_helpers_bash/test_variables.sh

# Prepare tests by cleaning up all files.
source ./test_helpers_bash/test_prepare_once.sh

# Initialize permanent files..
source ./test_helpers_bash/test_createvimrc.sh

TESTS=(
    test_bash/test_autopep8.sh
    # test_bash/test_folding.sh
    # test_autocommands.sh and test_pymodelint.sh migrated to Vader tests
    test_bash/test_textobject.sh
)

# Execute tests.
MAIN_RETURN=0
## now loop through the above array
for TEST in "${TESTS[@]}";
do
   source ./test_helpers_bash/test_prepare_between_tests.sh
   echo "Starting test: ${TEST##*/}" | tee -a "${VIM_OUTPUT_FILE}"
   bash "$(pwd)/${TEST}"
   R=$?
   MAIN_RETURN=$(( MAIN_RETURN + R ))
   echo -e "    ${TEST##*/}: Return code: ${R}\n" | tee -a "${VIM_OUTPUT_FILE}"
done

if [ -f "${VIM_DISPOSABLE_PYFILE}" ]; then
    rm "${VIM_DISPOSABLE_PYFILE}"
fi

echo "========================================================================="
echo "                                  RESULTS"
echo "========================================================================="

# Show return codes.
RETURN_CODES=$(grep -i "Return code" < "${VIM_OUTPUT_FILE}" | grep -v "Return code: 0")
echo -e "${RETURN_CODES}"

# Show errors:
E1=$(grep -E "^E[0-9]+:" "${VIM_OUTPUT_FILE}")
E2=$(grep -Ei "^Error" "${VIM_OUTPUT_FILE}")
if [[ "${MAIN_RETURN}" == "0" ]]; then
    echo "No errors."
else
    echo "Errors:"
    echo -e "    ${E1}\n    ${E2}"
fi

# Generate coverage.xml for codecov (basic structure)
# Note: Python-mode is primarily a Vim plugin, so coverage collection
# is limited. This creates a basic coverage.xml structure for CI.
# We're currently in tests/ directory (changed at line 8), so go up one level
PROJECT_ROOT="$(cd .. && pwd)"
COVERAGE_XML="${PROJECT_ROOT}/coverage.xml"
# Store PROJECT_ROOT in a way that will definitely expand
PROJECT_ROOT_VALUE="${PROJECT_ROOT}"

if command -v coverage &> /dev/null; then
    # Try to generate XML report if coverage data exists
    cd "${PROJECT_ROOT}"
    if [ -f .coverage ]; then
        coverage xml -o "${COVERAGE_XML}" 2>/dev/null || true
    fi
fi

# Always create coverage.xml (minimal if no coverage data)
if [ ! -f "${COVERAGE_XML}" ]; then
    cd "${PROJECT_ROOT}"
    printf '<?xml version="1.0" ?>\n' > "${COVERAGE_XML}"
    printf '<coverage version="7.0.0">\n' >> "${COVERAGE_XML}"
    printf '    <sources>\n' >> "${COVERAGE_XML}"
    printf '        <source>%s</source>\n' "${PROJECT_ROOT_VALUE}" >> "${COVERAGE_XML}"
    printf '    </sources>\n' >> "${COVERAGE_XML}"
    printf '    <packages/>\n' >> "${COVERAGE_XML}"
    printf '</coverage>\n' >> "${COVERAGE_XML}"
fi

# Exit the script with error if there are any return codes different from 0.
exit ${MAIN_RETURN}
# vim: set fileformat=unix filetype=sh wrap tw=0 :
