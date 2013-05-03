" DESC: Save file if it modified and run python code
fun! pymode#run#Run(line1, line2) "{{{
    if &modifiable && &modified
        try
            noautocmd write
        catch /E212/
            echohl Error | echo "File modified and I can't save it. Cancel code checking." | echohl None
            return 0
        endtry
    endif
    py import StringIO
    py sys.stdout, stdout_ = StringIO.StringIO(), sys.stdout
    py sys.stderr, stderr_ = StringIO.StringIO(), sys.stderr
    py enc = vim.eval('&enc')
    call setqflist([])
    call pymode#WideMessage("Code running.")
    try
        py context = globals()
        py context['raw_input'] = context['input'] = lambda s: vim.eval('input("{0}")'.format(s))
        py execfile(vim.eval('expand("%:p")'), context)
        py out, err = sys.stdout.getvalue().strip(), sys.stderr.getvalue()
        py sys.stdout, sys.stderr = stdout_, stderr_

        cexpr ""
        py for x in err.strip().split('\n'): vim.command('caddexpr "' + x.replace('"', r'\"') + '"')
        let l:oldefm = &efm
        set efm=%C\ %.%#,%A\ \ File\ \"%f\"\\,\ line\ %l%.%#,%Z%[%^\ ]%\\@=%m
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
