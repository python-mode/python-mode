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
    test_bash/test_autocommands.sh
    # test_bash/test_folding.sh
    test_bash/test_pymodelint.sh
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

# Exit the script with error if there are any return codes different from 0.
exit ${MAIN_RETURN}
# vim: set fileformat=unix filetype=sh wrap tw=0 :
