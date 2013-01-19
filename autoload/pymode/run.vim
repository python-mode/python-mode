" DESC: Save file if it modified and run python code
fun! pymode#run#Run(line1, line2) "{{{
    if &modifiable && &modified | write | endif	
    py import StringIO
    py sys.stdout, stdout_ = StringIO.StringIO(), sys.stdout
    py sys.stderr, stderr_ = StringIO.StringIO(), sys.stderr
    py enc = vim.eval('&enc')
    call pymode#WideMessage("Code running.")
    try
        py execfile(vim.eval('expand("%s:p")'))
        py out, err = sys.stdout.getvalue(), sys.stderr.getvalue()
        py sys.stdout, sys.stderr = stdout_, stderr_
        call pymode#TempBuffer()
        py vim.current.buffer.append([x.encode(enc) for x in out.split('\n')], 0)
        wincmd p
        let l:oldefm = &efm
        set efm=%C\ %.%#,%A\ \ File\ \"%f\"\\,\ line\ %l%.%#,%Z%[%^\ ]%\\@=%m
        cexpr ""
        py for x in err.split('\n'): vim.command('caddexpr "' + x.replace('"', r'\"') + '"')
        let &efm = l:oldefm
        call pymode#WideMessage("")
        8cwin

    catch /.*/

        echohl Error | echo "Run-time error." | echohl none
        
    endtry
endfunction "}}}
