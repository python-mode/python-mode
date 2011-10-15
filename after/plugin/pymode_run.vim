" DESC: Set scriptname
let g:scriptname = expand("<sfile>:t")

" OPTION: g:pymode_doc -- bool. Show documentation enabled
call helpers#SafeVar("g:pymode_run", 1)

" DESC: Disable script loading
if g:pymode_run == 0
    finish
endif

" DESC: Check python
if !helpers#CheckProgramm("python")
    let g:pymode_run = 0
    finish
endif

" OPTION: g:pymode_doc_key -- string. Key for show python documantation.
call helpers#SafeVar("g:pymode_run_key", "<leader>r")

" DESC: Save file if it modified and run python code
fun! pymode_run#Run() "{{{
    if &modifiable && &modified | write | endif	
    call helpers#ShowPreviewCmd(g:python . " " . expand("%:p"))
endfunction "}}}
