" Check python support
if !has('python')
    helpers#ShowError(s:scriptname . ' required vim compiled with +python.')
    finish
endif

" Check for pylint plugin is loaded
if helpers#SafeVar("b:pylint", 1)
    finish
endif

call helpers#SafeVar('g:pymode_lint_disable', '"C0103,C0111,C0301,W0141,W0142,W0212,W0221,W0223,W0232,W0401,W0613,W0631,E1101,E1120,R0903,R0904,R0913"')
call helpers#SafeVar('g:pymode_lint_members', '"REQUEST,acl_users,aq_parent,objects,DoesNotExist,_meta,status_code,content,context"')
call helpers#SafeVar('g:pymode_lint_cwindow', 1)
call helpers#SafeVar('g:pymode_lint_signs', 1)
call helpers#SafeVar('g:pymode_lint_write', 1)

if g:pymode_lint_write
    au BufWritePost <buffer> call <SID>:PyLint()
endif

command! PyLintToggle :let b:pylint_disabled = exists('b:pylint_disabled') ? b:pylint_disabled ? 0 : 1 : 1
command! PyLint :call <SID>:PyLint()

" Signs definition
sign define W text=WW texthl=Todo
sign define C text=CC texthl=Comment
sign define R text=RR texthl=Visual
sign define E text=EE texthl=Error

python << EOF
import StringIO

from logilab.astng.builder import MANAGER
from pylint import lint, checkers

linter = lint.PyLinter()
checkers.initialize(linter)
linter.set_option('output-format', 'parseable')
linter.set_option('disable', vim.eval("g:pymode_lint_disable"))
linter.set_option('reports', 0)

def check():
    target = vim.eval("expand('%:p')")
    MANAGER.astng_cache.clear()
    linter.reporter.out = StringIO.StringIO()
    linter.check(target)
    vim.command('let pylint_output = "%s"' % linter.reporter.out.getvalue())
EOF

function! <SID>:PyLint()

    if exists("b:pylint_disabled") && b:pylint_disabled == 1 | return | endif

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
    endif

    " Place signs
    if g:pymode_lint_signs
        call helpers#PlaceErrorSigns()
    endif

endfunction
