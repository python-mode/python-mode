" OPTION: g:pymode -- bool. Run pymode.
call helpers#SafeVar("g:pymode", 1)

let g:pymode_path = 0

" DESC: Disable script loading
if !g:pymode || g:pymode_path
    finish
endif

" DESC: Check python support
if !has('python')
    echoerr expand("<sfile>:t") . " required vim compiled with +python."
    echoerr "Pymode pylint and rope plugins will be disabled."
    let g:pymode = 0
    finish
endif
let g:pymode_path = 1

python << EOF
import sys, os, vim
sys.path.append(
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
