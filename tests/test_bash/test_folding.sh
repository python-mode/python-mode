#! /bin/bash

# Note: a solution with unix 'timeout' program was tried but it was unsuccessful. The problem with folding 4 is that in the case of a crash one expects the folding to just stay in an infinite loop, thus never existing with error. An improvement is suggested to this case.

function test_folding() {
    declare -a TEST_PYMODE_FOLDING_TESTS_ARRAY=(
        "test_procedures_vimscript/folding1.vim"
        "test_procedures_vimscript/folding2.vim"
        # "test_procedures_vimscript/folding3.vim"
        "test_procedures_vimscript/folding4.vim"
        )

    RETURN_CODE=0

    for SUB_TEST in "${TEST_PYMODE_FOLDING_TESTS_ARRAY[@]}"; do
        CONTENT="$(${VIM_BINARY:-vim} --not-a-term --clean -i NONE -u "${VIM_TEST_VIMRC}" -c "source $(pwd)/tests/${SUB_TEST}" "${VIM_DISPOSABLE_PYFILE}" 2>&1)"
        SUB_TEST_RETURN_CODE=$?
        echo -e "${CONTENT}" >> "${VIM_OUTPUT_FILE}"
        RETURN_CODE=$(( RETURN_CODE + SUB_TEST_RETURN_CODE ))
        echo -e "\tSubTest: $0:${SUB_TEST}: Return code: ${SUB_TEST_RETURN_CODE}" | tee -a "${VIM_OUTPUT_FILE}"
        bash ./test_helpers_bash/test_prepare_between_tests.sh
    done

    return ${RETURN_CODE}
}
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    test_folding
fi
# vim: set fileformat=unix filetype=sh wrap tw=0 :
