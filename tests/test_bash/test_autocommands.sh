#! /bin/bash

# TODO XXX: improve python-mode testing asap.
# Test all python commands.

# Execute tests.
declare -a TEST_PYMODE_COMMANDS_ARRAY=(
    "./test_procedures_vimscript/pymodeversion.vim"
    "./test_procedures_vimscript/pymodelint.vim"
    "./test_procedures_vimscript/pymoderun.vim"
    )

### Enable the following to execute one test at a time.
### FOR PINPOINT TESTING ### declare -a TEST_PYMODE_COMMANDS_ARRAY=(
### FOR PINPOINT TESTING ###     "./test_procedures_vimscript/pymoderun.vim"
### FOR PINPOINT TESTING ###     )

RETURN_CODE=0

## now loop through the above array
set +e
for ONE_PYMODE_COMMANDS_TEST in "${TEST_PYMODE_COMMANDS_ARRAY[@]}"
do
    CONTENT="$(vim --clean -i NONE -u "${VIM_TEST_VIMRC}" -c "source ${ONE_PYMODE_COMMANDS_TEST}" "${VIM_DISPOSABLE_PYFILE}" 2>&1)"

    ### Enable the following to execute one test at a time.
    ### FOR PINPOINT TESTING ### vim --clean -i NONE -u $VIM_TEST_VIMRC -c "source $ONE_PYMODE_COMMANDS_TEST" $VIM_DISPOSABLE_PYFILE
    ### FOR PINPOINT TESTING ### exit 1

    SUB_TEST_RETURN_CODE=$?
    echo -e "${CONTENT}" >> "${VIM_OUTPUT_FILE}"
    RETURN_CODE=$(( RETURN_CODE + SUB_TEST_RETURN_CODE ))
    echo -e "\tSubTest: $0:${ONE_PYMODE_COMMANDS_TEST}: Return code: ${SUB_TEST_RETURN_CODE}" | tee -a "${VIM_OUTPUT_FILE}"
    bash ./test_helpers_bash/test_prepare_between_tests.sh
done

exit ${RETURN_CODE}
# vim: set fileformat=unix filetype=sh wrap tw=0 :
