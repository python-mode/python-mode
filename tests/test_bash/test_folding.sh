#! /bin/bash

# Note: a solution with unix 'timeout' program was tried but it was unsuccessful. The problem with folding 4 is that in the case of a crash one expects the folding to just stay in an infinite loop, thus never existing with error. An improvement is suggested to this case.

# Source file.
set +e
source ./test_helpers_bash/test_prepare_between_tests.sh
vim -i NONE -u $VIM_TEST_VIMRC -c "source ./test_procedures_vimscript/folding1.vim" $VIM_DISPOSABLE_PYFILE > /dev/null
R1=$?
source ./test_helpers_bash/test_prepare_between_tests.sh
vim -i NONE -u $VIM_TEST_VIMRC -c "source ./test_procedures_vimscript/folding2.vim" $VIM_DISPOSABLE_PYFILE > /dev/null
R2=$?
source ./test_helpers_bash/test_prepare_between_tests.sh
# TODO: enable folding3.vim script back.
# vim -i NONE -u $VIM_TEST_VIMRC -c "source ./test_procedures_vimscript/folding3.vim" $VIM_DISPOSABLE_PYFILE > /dev/null
# R3=$?
source ./test_helpers_bash/test_prepare_between_tests.sh
vim -i NONE -u $VIM_TEST_VIMRC -c "source ./test_procedures_vimscript/folding4.vim" $VIM_DISPOSABLE_PYFILE > /dev/null
R4=$?
set -e

if [[ "$R1" -ne 0 ]]
then
    exit 1
elif [[ "$R2" -ne 0 ]]
then
    exit 2
# elif [[ "$R3" -ne 0 ]]
# then
#     exit 3
elif [[ "$R4" -ne 0 ]]
then
    exit 4
fi

# vim: set fileformat=unix filetype=sh wrap tw=0 :
