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
    helpers#ShowPreviewCmd(g:python . ' ' . expand('%:p'))
endfunction "}}}

" Map keys
nnoremap <silent> <buffer> <leader>r :call RunPython()<CR>
