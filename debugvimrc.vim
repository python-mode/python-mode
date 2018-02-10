" Use this settings for testing the plugin.
"
" Run vim with command:
"
" $ vim -u ./debug.vim /my/py/file.py
"
" Only python-mode will be loaded.

" Disable all persistence between sessions.
let skip_defaults_vim=1
" TODO XXX: this nevertheless keeps viminfo enabled. As a workaround the flag
" '-i NONE' should be added to vim's loading.
set viminfo=
set nobackup
set noswapfile

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

" IMPORTANT: Do note that the history of this session is saved on the log file.
" See the augroup in ./ftplugin/python/pymode.vim file.
