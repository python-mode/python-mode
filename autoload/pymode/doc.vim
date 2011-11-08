fun! pymode#doc#Show(word) "{{{
    if a:word == ''
        echoerr "No name/symbol under cursor!"
    else
        call pymode#ShowCommand(g:pydoc . " " . escape(a:word, " "))
    endif
endfunction "}}}
