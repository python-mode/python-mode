" Python-mode search by documentation


fun! pymode#doc#Show(word) "{{{
    if a:word == ''
        echoerr "No name/symbol under cursor!"
    else
        Python import StringIO
        Python sys.stdout, _ = StringIO.StringIO(), sys.stdout
        Python help(vim.eval('a:word'))
        call pymode#TempBuffer()
        Python vim.current.buffer.append(str(out).splitlines(), 0)
        wincmd p
    endif
endfunction "}}}


" vim: fdm=marker:fdl=0
