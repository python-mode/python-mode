#! /bin/bash

# TODO XXX: improve python-mode testing asap.
# Test all python commands.

# Source file.
set +e
# vim --clean -i NONE -u "${VIM_TEST_VIMRC}" -c "source ./test_procedures_vimscript/pymodelint.vim" "${VIM_DISPOSABLE_PYFILE}" >> "${VIM_OUTPUT_FILE}" 2>&1
CONTENT="$(vim --clean -i NONE -u "${VIM_TEST_VIMRC}" -c "source ./test_procedures_vimscript/pymodeversion.vim" "${VIM_DISPOSABLE_PYFILE}" 2>&1)"
RETURN_CODE=$?
echo -e "${CONTENT}" >> "${VIM_OUTPUT_FILE}"
set -e

exit ${RETURN_CODE}
# vim: set fileformat=unix filetype=sh wrap tw=0 :
