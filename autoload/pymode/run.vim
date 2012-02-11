" DESC: Save file if it modified and run python code
fun! pymode#run#Run(line1, line2) "{{{
    if &modifiable && &modified | write | endif	
    let f = expand("%:p")
    call pymode#TempBuffer()
    redi @">
    exe "sil!py execfile('" . l:f . "')"
    redi END
    normal Pdd
    wincmd p
endfunction "}}}
