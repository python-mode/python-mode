if !has('python')
    helpers#ShowError(s:scriptname . ' required vim compiled with +python.')
    finish
endif

if !helpers#CheckProgramm('pydoc')
    helpers#ShowError(s:scriptname . ' required pydoc.')
    finish
endif

if helpers#SafeVar("b:doc", 1)
    finish
endif

fun! <SID>:PydocLoad(word) "{{{
    if a:word == ''
        call helpers#ShowError('no name/symbol under cursor!')
        return 0
    endif
    call helpers#ShowPreviewCmd(g:pydoc . " " . escape(a:word, " "))
endfunction "}}}

command! -nargs=+ Pydoc call <SID>:PydocLoad("<args>")

nnoremap <silent> <buffer> K :call <SID>:PydocLoad(expand("<cword>"))<CR>
