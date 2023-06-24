#! /bin/bash

# Source file.
set +e
CONTENT="$(vim --clean -i NONE -u "${VIM_TEST_VIMRC}" -c "source ./test_procedures_vimscript/autopep8.vim" "${VIM_DISPOSABLE_PYFILE}" 2>&1)"
RETURN_CODE=$?
echo -e "${CONTENT}" >> "${VIM_OUTPUT_FILE}"
set -e

exit ${RETURN_CODE}
# vim: set fileformat=unix filetype=sh wrap tw=0 :
