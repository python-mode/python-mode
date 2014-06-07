" Python-mode search by documentation
"
PymodePython import pymode

fun! pymode#doc#find() "{{{
    " Extract the 'word' at the cursor, expanding leftwards across identifiers
    " and the . operator, and rightwards across the identifier only.
    "
    " For example:
    "   import xml.dom.minidom
    "           ^   !
    "
    " With the cursor at ^ this returns 'xml'; at ! it returns 'xml.dom'.
    let l:line = getline(".")
    let l:pre = l:line[:col(".") - 1]
    let l:suf = l:line[col("."):]
    let word = matchstr(pre, "[A-Za-z0-9_.]*$") . matchstr(suf, "^[A-Za-z0-9_]*")
    call pymode#doc#show(word)
endfunction "}}}

fun! pymode#doc#show(word) "{{{
    if a:word == ''
        call pymode#error("No name/symbol under cursor!")
        return 0
    endif

    call pymode#tempbuffer_open('__doc__')
    PymodePython pymode.get_documentation()
    setlocal nomodifiable
    setlocal nomodified
    setlocal filetype=rst
    wincmd p

endfunction "}}}
