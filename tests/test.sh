#! /bin/bash

# Check before starting.
set -e
which vim 1>/dev/null 2>/dev/null

# Set variables.
export VIM_TEST_FILE=/tmp/pymode.out
export VIM_TEST_VIMRC=/tmp/pymode_vimrc
export VIM_TEST_PYFILE=/tmp/pyfile.py
export VIM_TEST_PYMODECOMMANDS=/tmp/pymode_commands.txt

# Prepare tests.
set +e
rm $VIM_TEST_FILE $VIM_TEST_VIMRC $VIM_TEST_PYFILE $VIM_TEST_PYMODECOMMANDS 2&>/dev/null
set -e

# Create minimal vimrc.
echo "call has('python3')" >> $VIM_TEST_VIMRC
echo "set noswapfile" >> $VIM_TEST_VIMRC
echo "set shell=bash" >> $VIM_TEST_VIMRC
echo "set ft=python" >> $VIM_TEST_VIMRC
echo -e "syntax on\nfiletype plugin indent on\nset nocompatible" >> $VIM_TEST_VIMRC
echo -e "set runtimepath+=$(dirname $PWD)\n\n" >> $VIM_TEST_VIMRC
# echo "set runtimepath+=~/.vim/packpathdir/code/start/python-mode" >> $VIM_TEST_VIMRC

# Start tests.
echo "Starting vim tests."

# Iterate over each Pymode command.
set +e
vim -u $VIM_TEST_VIMRC -c "redir >> $VIM_TEST_PYMODECOMMANDS" -c "silent! command" -c "xall" $VIM_TEST_PYFILE
touch $VIM_TEST_PYFILE
while IFS= read -r PYCMD
do
    # Customize commands which require arguments.
    if [ $PYCMD == 'PymodeDoc' ];
    then
        export PYCMD="PymodeDoc unittest"
    elif [ $PYCMD == 'PymodeVirtualenv' ];
    then
        # export PYCMD="PymodeVirtualenv venv"
        :
    elif [ $PYCMD == 'PymodePython' ];
    then
        export PYCMD="PymodePython print(1 + 1)"
    fi
    echo "--------------- Processing $PYCMD" >> $VIM_TEST_FILE
    vim -n -E -u $VIM_TEST_VIMRC -c "redir >> $VIM_TEST_FILE" -c "$PYCMD" -c "xall" $VIM_TEST_PYFILE
    echo "" >> $VIM_TEST_FILE
    echo "---------------" >> $VIM_TEST_FILE
    echo -e "\n" >> $VIM_TEST_FILE
done < <(grep -o -E "Pymode[a-zA-Z]+" $VIM_TEST_PYMODECOMMANDS)
set -e

# echo "Test 1" >> $VIM_TEST_FILE
# vim -u $VIM_TEST_VIMRC -c "redir >> $VIM_TEST_FILE" -c "silent $PYCMD" -c "quitall" $VIM_TEST_PYFILE
# echo "" >> $VIM_TEST_FILE
#
# echo "Test 2" >> $VIM_TEST_FILE
# vim -u $VIM_TEST_VIMRC -c "redir >> $VIM_TEST_FILE" -c "scriptnames" -c "quit"
# echo "" >> $VIM_TEST_FILE

# Print errors.
echo "Errors:"
grep -E "^E[0-9]+:" $VIM_TEST_FILE

echo "Reched end of tests."

# Cleanup tests.
set +e
# rm $VIM_TEST_VIMRC $VIM_TEST_PYFILE $VIM_TEST_PYMODECOMMANDS 2&>/dev/null
set -e
vim $VIM_TEST_FILE

# vim: set fileformat=unix filetype=sh wrap tw=0:
