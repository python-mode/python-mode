#! /bin/bash

# TODO XXX: improve python-mode testing asap.
# Test all python commands.

# Source file.
set +e
vim -i NONE -u $VIM_TEST_VIMRC -c "source ./test_procedures_vimscript/pymodelint.vim" $VIM_DISPOSABLE_PYFILE
# RETURN_CODE=$(vim -i NONE -u $VIM_TEST_VIMRC -c "source ./test_procedures_vimscript/pymodeversion.vim" $VIM_DISPOSABLE_PYFILE > /dev/null 2>&1)
# RETURN_CODE=$?
set -e
# exit $RETURN_CODE

# vim: set fileformat=unix filetype=sh wrap tw=0 :
