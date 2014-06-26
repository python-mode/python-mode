if !g:pymode || !g:pymode_indent || exists("b:did_indent")
    finish
endif

let b:did_indent = 1

setlocal nolisp
setlocal tabstop=4
setlocal softtabstop=4
setlocal shiftwidth=4
setlocal shiftround
setlocal expandtab
setlocal autoindent
setlocal indentexpr=pymode#indent#get_indent(v:lnum)
setlocal indentkeys=!^F,o,O,<:>,0),0],0},=elif,=except
