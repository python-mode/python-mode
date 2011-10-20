" OPTION: g:pymode_lint -- bool. Load pylint plugin
call helpers#SafeVar("g:pymode_lint", 1)

" DESC: Disable script loading
if !g:pymode_lint || !g:pymode
    let g:pymode_lint = 0
    finish
endif

" OPTION: g:pymode_lint_write -- bool. Check code every save.
call helpers#SafeVar("g:pymode_lint_write", 1)

" OPTION: g:pymode_lint_cwindow -- bool. Auto open cwindow if errors find
call helpers#SafeVar("g:pymode_lint_cwindow", 1)

" OPTION: g:pymode_lint_signs -- bool. Place error signs
call helpers#SafeVar("g:pymode_lint_signs", 1)

" OPTION: g:pymode_lint_config -- str. Path to pylint config file
call helpers#SafeVar("g:pymode_lint_config", string($HOME . "/.pylintrc"))

" OPTION: g:pymode_lint_jump -- int. Jump on first error.
call helpers#SafeVar("g:pymode_lint_jump", 0)

" DESC: Signs definition
sign define W text=WW texthl=Todo
sign define C text=CC texthl=Comment
sign define R text=RR texthl=Visual
sign define E text=EE texthl=Error

" DESC: Set default pylint configuration
if !filereadable(g:pymode_lint_config)
    let g:pymode_lint_config = expand("<sfile>:p:h:h:h") . "/.pylintrc"
endif

python << EOF
import os
import StringIO

from logilab.astng.builder import MANAGER
from pylint import lint, checkers

linter = lint.PyLinter()
checkers.initialize(linter)
linter.set_option("output-format", "parseable")
linter.set_option("reports", 0)

linter.load_file_configuration(vim.eval("g:pymode_lint_config"))

def check():
    target = vim.eval("expand('%:p')")
    MANAGER.astng_cache.clear()
    linter.reporter.out = StringIO.StringIO()
    linter.check(target)
    pylint_output = linter.reporter.out.getvalue()
    vim.command('let pylint_output = "%s"' % pylint_output.replace('"', '\\"'))
EOF

" DESC: Check code
function! pymode_lint#Lint()

    if g:pymode_lint == 0 | return | endif

    if &modifiable && &modified | write | endif	
    cclose

    let pylint_output = ""
    let bufnum = bufnr("%")
    py check()
    let b:qf_list = []
    for error in split(pylint_output, "\n")
        let b:parts = matchlist(error, '\v([A-Za-z\.]+):(\d+): \[([EWRCI]+)[^\]]*\] (.*)')
        if len(b:parts) > 3
            let l:qf_item = {}
            let l:qf_item.filename = expand('%')
            let l:qf_item.bufnr = bufnum
            let l:qf_item.lnum = b:parts[2]
            let l:qf_item.type = b:parts[3]
            let l:qf_item.text = b:parts[4]
            call add(b:qf_list, l:qf_item)
        endif
    endfor

    call setqflist(b:qf_list, 'r')

    " Open cwindow
    if g:pymode_lint_cwindow && len(b:qf_list)
        botright cwindow
        if g:pymode_lint_jump
            cc
        endif
    endif

    " Place signs
    if g:pymode_lint_signs
        call helpers#PlaceErrorSigns()
    endif

endfunction
