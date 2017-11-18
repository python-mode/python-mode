" Use this settings for testing the plugin.
"
" Run vim with command:
"
" $ vim -u ./debug.vim /my/py/file.py
"
" Only python-mode will be loaded.

" Modify vimrc configuration.
execute('set rtp+='. expand('<sfile>:p:h'))
set rtp -=$HOME/.vim
set rtp -=$HOME/.vim/after
set nocompatible

" Activate debugging.
let g:pymode_debug = 1

" Define a common shell for non Windows systems.
if ! (has('win16') || has('win32') || has('win64'))
    set shell=/bin/bash
endif
