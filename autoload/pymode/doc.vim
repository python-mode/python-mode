" Python-mode search by documentation


fun! pymode#doc#Show(word) "{{{
    if a:word == ''
        echoerr "No name/symbol under cursor!"
    else
        call pymode#Execute("import StringIO")
        call pymode#Execute("sys.stdout, _ = StringIO.StringIO(), sys.stdout")
        call pymode#Execute("help('".a:word."')")
        call pymode#Execute("sys.stdout, out = _, sys.stdout.getvalue()")
        call pymode#TempBuffer()
        call pymode#Execute("vim.current.buffer.append(str(out).splitlines(), 0)")
        wincmd p
    endif
endfunction "}}}


" vim: fdm=marker:fdl=0
