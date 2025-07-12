#! /bin/bash

# TODO XXX: improve python-mode testing asap.
# Test all python commands.

function test_pymodelint() {
    # Source file.
    CONTENT="$(${VIM_BINARY:-vim} --not-a-term --clean -i NONE -u "${VIM_TEST_VIMRC}" -c "source ./test_procedures_vimscript/pymodelint.vim" "${VIM_DISPOSABLE_PYFILE}" 2>&1)"
    RETURN_CODE=$?
    echo -e "${CONTENT}" >> "${VIM_OUTPUT_FILE}"

    return ${RETURN_CODE}
}
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    test_pymodelint
fi
# vim: set fileformat=unix filetype=sh wrap tw=0 :
