#! /bin/bash

# Create minimal vimrc.
cat <<-EOF >> "${VIM_TEST_VIMRC}"
    syntax on
    filetype plugin indent on
    set nocompatible
    call has('python3')
    set paste
    set shortmess=at
    set cmdheight=10
    set ft=python
    set shell=bash
    set noswapfile
    set backupdir=
    set undodir=
    set viewdir=
    set directory=
    set runtimepath=
    set runtimepath+="$(dirname "${PWD}")"
    set packpath+=/tmp
    " redir! >> "${VIM_OUTPUT_FILE}"
    set verbosefile="${VIM_OUTPUT_FILE}"
    let g:pymode_debug = 1
    set nomore
EOF
# vim: set fileformat=unix filetype=sh wrap tw=0 :
