if exists('g:python_path') || !has('python')
    finish
endif
let g:python_path = 1

python << EOF
import sys, os, vim
sys.path.append(
    os.path.join(
        os.path.dirname(
            os.path.dirname(
                vim.eval("expand('<sfile>:p')"))),

        'pylibs'))
EOF
