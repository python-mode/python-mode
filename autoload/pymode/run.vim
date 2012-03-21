" DESC: Save file if it modified and run python code
fun! pymode#run#Run(line1, line2) "{{{
    if &modifiable && &modified | write | endif	
    redi @">
    sil!py execfile(vim.eval('expand("%s:p")'))
    redi END
    call pymode#TempBuffer()
    normal ""Pdd
    wincmd p
endfunction "}}}
