" DESC: Set scriptname
let g:scriptname = expand("<sfile>:t")

" OPTION: g:pymode_doc -- bool. Show documentation enabled
call helpers#SafeVar("g:pymode_doc", 1)

" DESC: Disable script loading
if !g:pymode_doc
    finish
endif

" DESC: Check pydoc installed
if !helpers#CheckProgramm("pydoc")
    let g:pymode_doc = 0
    finish
endif

" OPTION: g:pymode_doc_key -- string. Key for show python documantation.
call helpers#SafeVar("g:pymode_doc_key", "K")

" DESC: Show python documentation
" ARGS: word -- string, word for search
fun! pymode_doc#Show(word) "{{{
    if a:word == ''
        echoerr "no name/symbol under cursor!"
        return 0
    endif
    call helpers#ShowPreviewCmd(g:pydoc . " " . escape(a:word, " "))
endfunction "}}}
