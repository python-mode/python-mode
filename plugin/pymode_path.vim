let g:pymode_version = "0.4.0"
command! PymodeVersion echomsg "Current python-mode version: " . g:pymode_version

" OPTION: g:pymode -- bool. Run pymode.
call helpers#SafeVar("g:pymode", 1)

" DESC: Disable script loading
if !g:pymode
    finish
endif

" DESC: Check python support
if !has('python')
    echoerr expand("<sfile>:t") . " required vim compiled with +python."
    echoerr "Pymode pylint and rope plugins will be disabled."
    let g:pymode = 0
    finish
endif

python << EOF
import sys, os, vim
sys.path.insert(0,
    os.path.join(
        os.path.dirname(
            os.path.dirname(
                vim.eval("expand('<sfile>:p')"))),

        'pylibs'))
EOF

" Syntax highlight
let python_highlight_all=1
let python_highlight_exceptions=1
let python_highlight_builtins=1
