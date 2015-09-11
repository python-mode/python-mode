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

PymodePython from pymode.run import run_code


" DESC: Run python code
fun! pymode#run#code_run(line1, line2) "{{{

    let l:output = []
    let l:traceback = []
    call setqflist([])

    call pymode#wide_message("Code running ...")

    try

        PymodePython run_code()

        if len(l:output)
            call pymode#tempbuffer_open('__run__')
            call append(line('$'), l:output)
            normal dd
            wincmd p
        else
            call pymode#wide_message("No output.")
        endif

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

        call pymode#quickfix_open(0, g:pymode_quickfix_maxheight, g:pymode_quickfix_maxheight, 0)

        let &efm = l:_efm

    catch /E234/

        echohl Error | echo "Run-time error." | echohl none

    endtry

endfunction "}}}
