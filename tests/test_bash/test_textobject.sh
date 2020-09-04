#! /bin/bash

# Source file.
set +e
source ./test_helpers_bash/test_prepare_between_tests.sh
vim --clean -i NONE -u $VIM_TEST_VIMRC -c "source ./test_procedures_vimscript/textobject.vim" $VIM_DISPOSABLE_PYFILE > /dev/null
R1=$?
set -e

if [[ "$R1" -ne 0 ]]
then
    exit 1
fi

# vim: set fileformat=unix filetype=sh wrap tw=0 :
