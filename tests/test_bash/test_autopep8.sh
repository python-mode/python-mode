#! /bin/bash

# Source file.
set +e
RETURN_CODE=$(vim -i NONE -u $VIM_TEST_VIMRC -c "source ./test_procedures_vimscript/autopep8.vim" $VIM_DISPOSABLE_PYFILE > /dev/null 2>&1)
RETURN_CODE=$?
set -e
exit $RETURN_CODE

# vim: set fileformat=unix filetype=sh wrap tw=0 :
