#! /bin/bash

# Source file.
set +e
# shellcheck source=../test_helpers_bash/test_prepare_between_tests.sh
source ./test_helpers_bash/test_prepare_between_tests.sh
CONTENT="$(vim --clean -i NONE -u "${VIM_TEST_VIMRC}" -c "source ./test_procedures_vimscript/textobject.vim" "${VIM_DISPOSABLE_PYFILE}" 2>&1)"
RETURN_CODE=$?
echo -e "${CONTENT}" >> "${VIM_OUTPUT_FILE}"
set -e

exit ${RETURN_CODE}
# vim: set fileformat=unix filetype=sh wrap tw=0 :
