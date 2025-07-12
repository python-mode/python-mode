#! /bin/bash

function test_autopep8() {
    # Source file.
    TEST_PROCEDURE="$(pwd)/test_procedures_vimscript/autopep8.vim"
    CONTENT="$(${VIM_BINARY:-vim} --not-a-term --clean -i NONE -u "${VIM_TEST_VIMRC}" -c "source ${TEST_PROCEDURE}" "${VIM_DISPOSABLE_PYFILE}" 2>&1)"
    RETURN_CODE=$?
    return ${RETURN_CODE}
}
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    test_autopep8
fi
# vim: set fileformat=unix filetype=sh wrap tw=0 :
