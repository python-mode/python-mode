" Python-mode search by documentation


fun! pymode#doc#Show(word) "{{{
    if a:word == ''
        echoerr "No name/symbol under cursor!"
    else
        py import StringIO
        py sys.stdout, _ = StringIO.StringIO(), sys.stdout
        py help(vim.eval('a:word'))
        py sys.stdout, out = _, sys.stdout.getvalue()
        call pymode#TempBuffer()
        py vim.current.buffer.append(str(out).split('\n'), 0)
        wincmd p
    endif
endfunction "}}}


" vim: fdm=marker:fdl=0
