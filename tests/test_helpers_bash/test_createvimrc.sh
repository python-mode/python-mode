#! /bin/bash

# Create minimal vimrc.
cat <<-EOF >> "${VIM_TEST_VIMRC}"
    " redir! >> "${VIM_OUTPUT_FILE}"
    call has('python3')
    filetype plugin indent on
    let g:pymode_debug = 1
    set backupdir=
    set cmdheight=10
    set directory=
    set ft=python
    set nocompatible
    set nomore
    set noswapfile
    set packpath+=/tmp
    set paste
    set runtimepath+="$(dirname "${PWD}")"
    set runtimepath=
    set shell=bash
    set shortmess=at
    set undodir=
    set verbosefile="${VIM_OUTPUT_FILE}"
    set viewdir=
    syntax on
EOF
# vim: set fileformat=unix filetype=sh wrap tw=0 :
