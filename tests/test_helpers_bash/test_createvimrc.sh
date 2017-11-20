#! /bin/bash

# Create minimal vimrc.
echo "call has('python3')" >> $VIM_TEST_VIMRC
echo "set noswapfile" >> $VIM_TEST_VIMRC
echo "set shell=bash" >> $VIM_TEST_VIMRC
echo "set ft=python" >> $VIM_TEST_VIMRC
echo -e "syntax on\nfiletype plugin indent on\nset nocompatible" >> $VIM_TEST_VIMRC
echo -e "set runtimepath+=$(dirname $PWD)\n" >> $VIM_TEST_VIMRC
echo -e "set verbosefile=$VIM_OUTPUT_FILE\n" >> $VIM_TEST_VIMRC

# vim: set fileformat=unix filetype=sh wrap tw=0 :
