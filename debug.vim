" Use this settings for testing the plugin.
" Run vim with command
"
" $ vim -u debug.py
"
" Only python-mode will be loaded.


execute('set rtp+='. expand('<sfile>:p:h'))
set rtp -=$HOME/.vim
set rtp -=$HOME/.vim/after
set nocp
syntax enable
