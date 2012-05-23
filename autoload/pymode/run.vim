" DESC: Save file if it modified and run python code
fun! pymode#run#Run(line1, line2) "{{{
    if &modifiable && &modified | write | endif	
    py import StringIO
    py sys.stdout, _ = StringIO.StringIO(), sys.stdout
    py execfile(vim.eval('expand("%s:p")'), {}, {})
    py sys.stdout, out = _, sys.stdout.getvalue()
    call pymode#TempBuffer()
    py vim.current.buffer.append(out.split('\n'), 0)
    wincmd p
endfunction "}}}
