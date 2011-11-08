" OPTION: g:pymode_lint -- bool. Load pylint plugin
call helpers#SafeVar("g:pymode_lint", 1)

" DESC: Disable script loading
if !g:pymode_lint || !g:pymode
    let g:pymode_lint = 0
    finish
endif

" OPTION: g:pymode_lint_write -- bool. Check code every save.
call helpers#SafeVar("g:pymode_lint_write", 1)

" OPTION: g:pymode_lint_checker -- str. Use pylint of pyflakes for check.
call helpers#SafeVar("g:pymode_lint_checker", "pylint")

" OPTION: g:pymode_lint_cwindow -- bool. Auto open cwindow if errors find
call helpers#SafeVar("g:pymode_lint_cwindow", 1)

" OPTION: g:pymode_lint_signs -- bool. Place error signs
call helpers#SafeVar("g:pymode_lint_signs", 1)

" OPTION: g:pymode_lint_config -- str. Path to pylint config file
call helpers#SafeVar("g:pymode_lint_config", $HOME . "/.pylintrc")

" OPTION: g:pymode_lint_jump -- int. Jump on first error.
call helpers#SafeVar("g:pymode_lint_jump", 0)

" OPTION: g:pymode_lint_minheight -- int. Minimal height of pymode lint window
call helpers#SafeVar("g:pymode_lint_minheight", 3)

" OPTION: g:pymode_lint_maxheight -- int. Maximal height of pymode lint window
call helpers#SafeVar("g:pymode_lint_maxheight", 6)

if g:pymode_lint_signs

    " DESC: Signs definition
    sign define W text=WW texthl=Todo
    sign define C text=CC texthl=Comment
    sign define R text=RR texthl=Visual
    sign define E text=EE texthl=Error

endif

" DESC: Set default pylint configuration
if !filereadable(g:pymode_lint_config)
    let g:pymode_lint_config = expand("<sfile>:p:h:h:h") . "/pylintrc"
endif

python << EOF
import os
import StringIO
import _ast
import re

from logilab.astng.builder import MANAGER
from pylint import lint, checkers
from pyflakes import checker


# Pylint setup
linter = lint.PyLinter()
pylint_re = re.compile('^[^:]+:(\d+): \[([EWRCI]+)[^\]]*\] (.*)$')

checkers.initialize(linter)
linter.set_option("output-format", "parseable")
linter.set_option("reports", 0)
linter.load_file_configuration(vim.eval("g:pymode_lint_config"))

# Pyflakes setup

# Pylint check
def pylint():
    filename = vim.current.buffer.name
    MANAGER.astng_cache.clear()
    linter.reporter.out = StringIO.StringIO()
    linter.check(filename)
    qf = []
    for w in linter.reporter.out.getvalue().split('\n'):
        test = pylint_re.match(w)
        test and qf.append(dict(
                filename = filename,
                bufnr = vim.current.buffer.number,
                lnum = test.group(1),
                type = test.group(2),
                text = test.group(3),
            ))
    vim.command('let b:qf_list = %s' % repr(qf))

# Pyflakes check
def pyflakes():
    filename = vim.current.buffer.name
    codeString = file(filename, 'U').read() + '\n'
    try:
        tree = compile(codeString, filename, "exec", _ast.PyCF_ONLY_AST)
    except SyntaxError, value:
        msg = value.args[0]
        if text is None:
            vim.command('echoerr "%s: problem decoding source"' % filename)
        else:
            lineno, _, text = value.lineno, value.offset, value.text
            line = text.splitlines()[-1]
            vim.command('echoerr "%s:%d: %s"' % (filename, lineno, msg))
            vim.command('echoerr "%s"' % line)
    else:
        w = checker.Checker(tree, filename)
        w.messages.sort(lambda a, b: cmp(a.lineno, b.lineno))
        qf = [dict(
            filename = filename,
            bufnr = vim.current.buffer.number,
            lnum = str(w.lineno),
            text = w.message % w.message_args,
            type = 'E'
        ) for w in w.messages]
        vim.command('let b:qf_list = %s' % repr(qf))

EOF

" DESC: Check code
function! pymode_lint#Lint()

    if g:pymode_lint == 0 | return | endif

    if &modifiable && &modified | write | endif	
    cclose

    let pylint_output = ""
    let bufnum = bufnr("%")
    exe "py ".g:pymode_lint_checker."()"
    call setqflist(b:qf_list, 'r')

    " Open cwindow
    if g:pymode_lint_cwindow && len(b:qf_list)
        botright cwindow
        exe max([min([line("$"), g:pymode_lint_maxheight]), g:pymode_lint_maxheight]) . "wincmd _"
        if g:pymode_lint_jump
            cc
        endif
    endif

    " Place signs
    if g:pymode_lint_signs
        call helpers#PlaceErrorSigns()
    endif

endfunction


fun! pymode_lint#Toggle() "{{{
    let g:pymode_lint = g:pymode_lint ? 0 : 1
    if g:pymode_lint
        echomsg "PyLint enabled."
    else
        echomsg "PyLint disabled."
    endif
endfunction "}}}

fun! pymode_lint#ToggleChecker() "{{{
    let g:pymode_lint_checker = g:pymode_lint_checker == "pylint" ? "pyflakes" : "pylint"
    echomsg "PyLint checker: " . g:pymode_lint_checker
endfunction "}}}
