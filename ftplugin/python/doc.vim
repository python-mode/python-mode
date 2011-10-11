" DESC: Set scriptname
let g:scriptname = expand('<sfile>:t')

" OPTION: g:pymode_doc -- bool. Show documentation enabled
call helpers#SafeVar('g:pymode_doc', 1)

" OPTION: g:pymode_doc_key -- string. Key for show python documantation.
call helpers#SafeVar('g:pymode_doc_key', "'K'")

" DESC: Disable script loading
if helpers#SafeVar("b:doc", 1) || g:pymode_doc == 0
    finish
endif

" DESC: Check pydoc installed
if !helpers#CheckProgramm('pydoc')
    finish
endif

" DESC: Show python documentation
" ARGS: word -- string, word for search
fun! <SID>:PydocLoad(word) "{{{
    if a:word == ''
        echoerr 'no name/symbol under cursor!'
        return 0
    endif
    call helpers#ShowPreviewCmd(g:pydoc . " " . escape(a:word, " "))
endfunction "}}}

" DESC: Set commands
command! -buffer -nargs=+ Pydoc call <SID>:PydocLoad("<args>")

" DESC: Set keys
exe "nnoremap <silent> <buffer> " g:pymode_doc_key ":call <SID>:PydocLoad(expand('<cword>'))<CR>"
