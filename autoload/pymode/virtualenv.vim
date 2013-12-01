" Support virtualenv
"
PymodePython from pymode.virtualenv import enable_virtualenv

fun! pymode#virtualenv#init() "{{{
    if !g:pymode_virtualenv || g:pymode_virtualenv_path == ""
        return
    endif

    PymodePython enable_virtualenv()

endfunction "}}}

fun! pymode#virtualenv#activate(relpath) "{{{
    let g:pymode_virtualenv_path = getcwd() . '/' . a:relpath
    call pymode#virtualenv#init()
endfunction "}}}
