fun! pymode#doc#Show(word) "{{{
    if a:word == ''
        echoerr "No name/symbol under cursor!"
    else
        call pymode#TempBuffer()
        redi @">
        sil!py help(vim.eval('a:word'))
        redi END
        normal Pdd
        wincmd p
    endif
endfunction "}}}
