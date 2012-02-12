fun! pymode#doc#Show(word) "{{{
    if a:word == ''
        echoerr "No name/symbol under cursor!"
    else
        py sys.stdout, _ = StringIO.StringIO(), sys.stdout
        py help(vim.eval('a:word'))
        py sys.stdout, out = _, sys.stdout.getvalue()
        redi @">
        sil!py print out
        redi END
        call pymode#TempBuffer()
        normal Pdd
        wincmd p
    endif
endfunction "}}}
