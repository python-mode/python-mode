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
        py sys.stdout, sys.stderr, out, err = stdout_, stderr_, sys.stdout.getvalue(), sys.stderr.getvalue()
        call pymode#TempBuffer()
        py vim.current.buffer.append([x.encode(enc) for x in out.split('\n')], 0)
        py if err.strip(): vim.current.buffer.append(['>>>' + x.encode(enc) for x in err.strip().split('\n')], 0)
        wincmd p
        call pymode#WideMessage("")

    catch /.*/

        echohl Error | echo "Run-time error." | echohl none
        
    endtry
endfunction "}}}
