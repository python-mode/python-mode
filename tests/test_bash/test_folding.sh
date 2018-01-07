#! /bin/bash

# Source file.
set +e
source ./test_helpers_bash/test_prepare_between_tests.sh
vim -i NONE -u $VIM_TEST_VIMRC -c "source ./test_procedures_vimscript/folding1.vim" $VIM_DISPOSABLE_PYFILE > /dev/null
R1=$?
source ./test_helpers_bash/test_prepare_between_tests.sh
vim -i NONE -u $VIM_TEST_VIMRC -c "source ./test_procedures_vimscript/folding2.vim" $VIM_DISPOSABLE_PYFILE > /dev/null
R2=$?
source ./test_helpers_bash/test_prepare_between_tests.sh
vim -i NONE -u $VIM_TEST_VIMRC -c "source ./test_procedures_vimscript/folding3.vim" $VIM_DISPOSABLE_PYFILE > /dev/null
R3=$?
set -e

if [[ "$R1" -ne 0 ]]
then
    exit 1
elif [[ "$R2" -ne 0 ]]
then
    exit 2
elif [[ "$R3" -ne 0 ]]
then
    exit 3
fi

# vim: set fileformat=unix filetype=sh wrap tw=0 :
