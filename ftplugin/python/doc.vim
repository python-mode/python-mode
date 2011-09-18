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

    let cmd = "pclose | botright 10new __doc__ | r!" . escape(g:pydoc, " ")
    let cmd = cmd . " " . escape(a:word, " ")
    silent exec cmd
    setlocal buftype=nofile bufhidden=wipe noswapfile nowrap previewwindow
    normal gg

endfunction "}}}

com! -nargs=+ Pydoc call <SID>:PydocLoad("<args>")

nnoremap <silent> <buffer> K :call <SID>:PydocLoad(expand("<cword>"))<CR>
