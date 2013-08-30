" Python-mode search by documentation


fun! pymode#doc#Show(word) "{{{
    if a:word == ''
        echoerr "No name/symbol under cursor!"
    else
        Python import StringIO
        Python sys.stdout, _ = StringIO.StringIO(), sys.stdout
        Python help(vim.eval('a:word'))
        Python sys.stdout, out = _, sys.stdout.getvalue()
        if !g:pymode_test
            call pymode#TempBuffer()
        endif
        Python vim.current.buffer.append(str(out).splitlines(), 0)
        wincmd p
    endif
endfunction "}}}


" vim: fdm=marker:fdl=0
