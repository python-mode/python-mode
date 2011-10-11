" DESC: Set scriptname
let g:scriptname = expand('<sfile>:t')

" OPTION: g:pymode_doc -- bool. Show documentation enabled
call helpers#SafeVar('g:pymode_run', 1)

" OPTION: g:pymode_doc_key -- string. Key for show python documantation.
call helpers#SafeVar('g:pymode_run_key', "'<leader>r'")

" DESC: Disable script loading
if helpers#SafeVar("b:run", 1) || g:pymode_run == 0
    finish
endif

" DESC: Check python
if !helpers#CheckProgramm('python')
    finish
endif

" DESC: Save file if it modified and run python code
fun! <SID>:RunPython() "{{{
    if &modifiable && &modified | write | endif	
    call helpers#ShowPreviewCmd(g:python . ' ' . expand('%:p'))
endfunction "}}}

" DESC: Set commands
command! -buffer Pyrun call <SID>:RunPython()

" DESC: Set keys
exe "nnoremap <silent> <buffer> " g:pymode_run_key ":call <SID>:RunPython()<CR>"
