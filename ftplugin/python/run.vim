" Check this script already load
if helpers#SafeVar("b:run", 1)
    finish
endif

" Check python
if !helpers#CheckProgramm('python')
    helpers#ShowError(s:scriptname . ' required python installed.')
    finish
endif

" DESC: Save and run python code
fun! RunPython() "{{{
    if &modifiable && &modified | write | endif	
    let output = system(g:python . ' ' . expand('%:p'))
    pclose | botright 8new
    setlocal buftype=nofile bufhidden=wipe noswapfile nowrap previewwindow
    put! =output
    $del
    wincmd p
endfunction "}}}

" Map keys
nnoremap <silent> <buffer> <leader>r :call RunPython()<CR>
