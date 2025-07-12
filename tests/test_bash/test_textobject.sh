#! /bin/bash

function test_textobject() {
    # Source file.
    # shellcheck source=../test_helpers_bash/test_prepare_between_tests.sh
    source ./test_helpers_bash/test_prepare_between_tests.sh
    CONTENT="$(${VIM_BINARY:-vim} --not-a-term --clean -i NONE -u "${VIM_TEST_VIMRC}" -c "source ./test_procedures_vimscript/textobject.vim" "${VIM_DISPOSABLE_PYFILE}" 2>&1)"
    RETURN_CODE=$?
    echo -e "${CONTENT}" >> "${VIM_OUTPUT_FILE}"

    return ${RETURN_CODE}
}
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    test_textobject
fi
# vim: set fileformat=unix filetype=sh wrap tw=0 :
