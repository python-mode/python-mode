" DESC: Save file if it modified and run python code
fun! pymode#run#Run(line1, line2) "{{{
    " There is no need to save the file first. We will load the code to be run
    " directly from the buffer, as a string, below
    py import StringIO
    py sys.stdout, stdout_ = StringIO.StringIO(), sys.stdout
    py sys.stderr, stderr_ = StringIO.StringIO(), sys.stderr
    py enc = vim.eval('&enc')
    call setqflist([])
    call pymode#WideMessage("Code running.")
    " Get the lines to be executed from the current buffer
    let l:code = getline(a:line1, a:line2)
    try
        py context = globals()
        " do we really want to use globals here? This passes the whole of
        " vim's current context to the python script.  Perhaps an empty dict
        " would be better
        py context['raw_input'] = context['input'] = lambda s: vim.eval('input("{0}")'.format(s))

python << ENDPYTHON
try:
        # Compiling the code here allows us to associate a filename with it, so that any
        # error messages that are raised refer to the correct file, rather than <string>. A
        # syntax error in the code will still appear to come from a file called <string>, but
        # we deal with that later.
        code = compile('\n'.join(vim.eval('l:code')) + '\n', vim.current.buffer.name, 'exec')
        exec(code, context)
# Vim cannot handle a SystemExit error raised by Python, so we need to trap it here, and
# handle it specially
except SystemExit as e:
    if e.code:
        # A non-false code indicates abnormal termination. A false code will be treated as a
        # successful run, and the error will be hidden from Vim
        vim.command('echohl Error | echo "Script exited with code {0}" | echohl none'.format(e.code))
        vim.command('return')
ENDPYTHON
        py out, err = sys.stdout.getvalue().strip(), sys.stderr.getvalue()
        py sys.stdout, sys.stderr = stdout_, stderr_
        cexpr ""
        let l:traceback = []
        let l:oldefm = &efm

        " The following lines set Vim's errorformat variable, to allow the
        " quickfix window to show Python tracebacks properly. It is much
        " easier to use let than set, because set requires many more
        " characters to be escaped. This is much easier to read and
        " maintain. % escapes are still needed however before any regex meta
        " characters. Hence \S (non-whitespace) becomes %\S etc.  Note that
        " * becomes %#, so .* (match any character) becomes %.%#  Commas must
        " also be escaped, with a backslash (\,). See the Vim help on
        " quickfix for details.
        "
        " Python errors are multi-lined. They often start with 'Traceback', so
        " we want to capture that (with +G) and show it in the quickfix window
        " because it explains the order of error messages.
        let &efm  = '%+GTraceback%.%#,'

        " The error message itself starts with a line with 'File' in it. There
        " are a couple of variations, and we need to process a line beginning
        " with whitespace followed by File, the filename in "", a line number,
        " and optional further text. %E here indicates the start of a multi-line
        " error message. The %\C at the end means that a case-sensitive search is
        " required.
        let &efm .= '%E  File "%f"\, line %l\,%m%\C,'
        let &efm .= '%E  File "%f"\, line %l%\C,'

        " The possible continutation lines are idenitifed to Vim by %C. We deal
        " with these in order of most to least specific to ensure a proper
        " match. A pointer (^) identifies the column in which the error occurs
        " (but will not be entirely accurate due to indention of Python code).
        let &efm .= '%C%p^,'

        " Any text, indented by more than two spaces contain useful information.
        " We want this to appear in the quickfix window, hence %+.
        let &efm .= '%+C    %.%#,'
        let &efm .= '%+C  %.%#,'

        " The last line (%Z) does not begin with any whitespace. We use a zero
        " width lookahead (\&) to check this. The line contains the error
        " message itself (%m)
        let &efm .= '%Z%\S%\&%m,'

        " We can ignore any other lines (%-G)
        let &efm .= '%-G%.%#'

python << ENDPYTHON2
# Remove any lines from the error output which contain the line
# "<string>". In this way a traceback from a syntax error will
# look just like a normal python traceback Add the other lines
# to a Vim list.
for x in [i for i in err.splitlines() if "<string>" not in i]:
    vim.command("call add(l:traceback, '{}')".format(x))
ENDPYTHON2
" Now we can add the list of errors to the quickfix window, and show it. We have
" to add them all at once in this way, because the errors are multi-lined and
" they won't be parsed properly otherwise.
        cgetexpr(l:traceback)
        call pymode#QuickfixOpen(0, g:pymode_lint_hold, g:pymode_lint_maxheight, g:pymode_lint_minheight, 0)
        let &efm = l:oldefm

python << EOF
if out:
    vim.command("call pymode#TempBuffer()")
    vim.current.buffer.append([x.decode("utf-8").encode(enc) for x in out.split('\n')], 0)
    vim.command("wincmd p")
else:
    vim.command('call pymode#WideMessage("No output.")')
EOF

    catch /.*/

        echohl Error | echo "Run-time error." | echohl none

    endtry
endfunction "}}}
