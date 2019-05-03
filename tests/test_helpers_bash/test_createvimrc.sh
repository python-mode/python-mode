#! /bin/bash

# Create minimal vimrc.
echo -e "syntax on\nfiletype plugin indent on\nset nocompatible" >> $VIM_TEST_VIMRC
echo "call has('python3')" >> $VIM_TEST_VIMRC
echo "set paste" >> $VIM_TEST_VIMRC
echo "set shortmess=at" >> $VIM_TEST_VIMRC
echo "set cmdheight=10" >> $VIM_TEST_VIMRC
echo "set ft=python" >> $VIM_TEST_VIMRC
echo "set shell=bash" >> $VIM_TEST_VIMRC
echo "set noswapfile" >> $VIM_TEST_VIMRC
echo "set backupdir=" >> $VIM_TEST_VIMRC
echo "set undodir=" >> $VIM_TEST_VIMRC
echo "set viewdir=" >> $VIM_TEST_VIMRC
echo "set directory=" >> $VIM_TEST_VIMRC
echo -e "set runtimepath=" >> $VIM_TEST_VIMRC
echo -e "set runtimepath+=$(dirname $PWD)\n" >> $VIM_TEST_VIMRC
echo -e "set packpath+=/tmp\n" >> $VIM_TEST_VIMRC
# echo -e "redir! >> $VIM_OUTPUT_FILE\n" >> $VIM_TEST_VIMRC
echo -e "set verbosefile=$VIM_OUTPUT_FILE\n" >> $VIM_TEST_VIMRC
echo -e "let g:pymode_debug = 1" >> $VIM_TEST_VIMRC

echo "set nomore" >> $VIM_TEST_VIMRC


# vim: set fileformat=unix filetype=sh wrap tw=0 :
