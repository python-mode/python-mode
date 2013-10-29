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
let s:efm  = '%+GTraceback%.%#,'

" The error message itself starts with a line with 'File' in it. There
" are a couple of variations, and we need to process a line beginning
" with whitespace followed by File, the filename in "", a line number,
" and optional further text. %E here indicates the start of a multi-line
" error message. The %\C at the end means that a case-sensitive search is
" required.
let s:efm .= '%E  File "%f"\, line %l\,%m%\C,'
let s:efm .= '%E  File "%f"\, line %l%\C,'

" The possible continutation lines are idenitifed to Vim by %C. We deal
" with these in order of most to least specific to ensure a proper
" match. A pointer (^) identifies the column in which the error occurs
" (but will not be entirely accurate due to indention of Python code).
let s:efm .= '%C%p^,'
" Any text, indented by more than two spaces contain useful information.
" We want this to appear in the quickfix window, hence %+.
let s:efm .= '%+C    %.%#,'
let s:efm .= '%+C  %.%#,'

" The last line (%Z) does not begin with any whitespace. We use a zero
" width lookahead (\&) to check this. The line contains the error
" message itself (%m)
let s:efm .= '%Z%\S%\&%m,'

" We can ignore any other lines (%-G)
let s:efm .= '%-G%.%#'


" DESC: Save file if it modified and run python code
fun! pymode#run#Run(line1, line2) "{{{
    let l:code = getline(a:line1, a:line2)
    let l:traceback = []

    call setqflist([])
    call pymode#WideMessage("Code running.")

    try

        Python << EOF

import StringIO, json

_input = lambda s: vim.eval('input("%s")' % s)
context = dict(__name__='__main__', input=_input, raw_input=_input)
out, errors = "", []
sys.stdout, stdout_ = StringIO.StringIO(), sys.stdout
sys.stderr, stderr_ = StringIO.StringIO(), sys.stderr

lines = [l.rstrip() for l in vim.eval('l:code')]
indent = 0
for line in lines:
    if line:
        indent = len(line) - len(line.lstrip())
        break

lines = [l[indent:] for l in lines]

try:
    code = compile('\n'.join(lines) + '\n', vim.current.buffer.name, 'exec')
    exec(code, context)

except SystemExit as e:
    errors.append('test')
    if e.code:
        # A non-false code indicates abnormal termination. A false code will be treated as a
        # successful run, and the error will be hidden from Vim
        vim.command('echohl Error | echo "Script exited with code {0}" | echohl none'.format(e.code))
        vim.command('return')

except Exception as e:
    import traceback
    err = traceback.format_exc()

else:
    err = sys.stderr.getvalue()

out = sys.stdout.getvalue().strip()
errors += [e for e in err.splitlines() if e and "<string>" not in e]

sys.stdout, sys.stderr = stdout_, stderr_

for e in errors:
    vim.command("call add(l:traceback, %s)" % json.dumps(e))

if out:
    vim.command("call pymode#TempBuffer()")
    vim.current.buffer.append([x.decode("utf-8").encode(vim.eval('&enc')) for x in out.split('\n')], 0)
    vim.command("wincmd p")
else:
    vim.command('call pymode#WideMessage("No output.")')

EOF

        cexpr ""

        let l:_efm = &efm

        let &efm = s:efm

        cgetexpr(l:traceback)
" If a range is run (starting other than at line 1), fix the reported error line numbers for
" the current buffer
        if a:line1 > 1
            let qflist = getqflist()
            for i in qflist
                if i.bufnr == bufnr("")
                    let i.lnum = i.lnum - 1 + a:line1
                endif
            endfor
            call setqflist(qflist)
        endif

        call pymode#QuickfixOpen(0, g:pymode_lint_hold, g:pymode_lint_maxheight, g:pymode_lint_minheight, 0)
        let &efm = l:_efm

    catch /E234/

        echohl Error | echo "Run-time error." | echohl none

    endtry

endfunction "}}}
