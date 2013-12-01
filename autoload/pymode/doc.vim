" Python-mode search by documentation
"
PymodePython import pymode

fun! pymode#doc#show(word) "{{{
    if a:word == ''
        call pymode#error("No name/symbol under cursor!")
    else
        call pymode#tempbuffer_open('__doc__')
        PymodePython pymode.get_documentation()
        setlocal nomodifiable
        setlocal nomodified
        setlocal filetype=rst
        wincmd p
    endif
endfunction "}}}

