function! pymode#lint#Check()
    if g:pymode_lint == 0 | return | endif
    if &modifiable && &modified
        try
            write
        catch /E212/
            echohl Error | echo "File modified and I can't save it. PyLint cancel." | echohl None
            return 0
        endtry
    endif	
    exe "py ".g:pymode_lint_checker."()"
    call setqflist(b:qf_list, 'r')
    if g:pymode_lint_cwindow
        call pymode#QuickfixOpen(0, 0, g:pymode_lint_maxheight, g:pymode_lint_minheight, g:pymode_lint_jump)
    endif
    if g:pymode_lint_signs
        call pymode#PlaceSigns()
    endif
endfunction

fun! pymode#lint#Toggle() "{{{
    let g:pymode_lint = g:pymode_lint ? 0 : 1
    if g:pymode_lint
        echomsg "PyLint enabled."
    else
        echomsg "PyLint disabled."
    endif
endfunction "}}}

fun! pymode#lint#ToggleChecker() "{{{
    let g:pymode_lint_checker = g:pymode_lint_checker == "pylint" ? "pyflakes" : "pylint"
    echomsg "PyLint checker: " . g:pymode_lint_checker
endfunction "}}}
