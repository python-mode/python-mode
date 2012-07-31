fun! pymode#lint#Check() "{{{
    " DESC: Run checkers on current file.
    "
    if !g:pymode_lint | return | endif

    if &modifiable && &modified
        try
            write
        catch /E212/
            echohl Error | echo "File modified and I can't save it. Cancel code checking." | echohl None
            return 0
        endtry
    endif

    let g:pymode_lint_buffer = bufnr('%')

    py lint.check_file()

endfunction " }}}


fun! pymode#lint#Parse()
    " DESC: Parse result of code checking.
    "
    call setqflist(g:qf_list, 'r')

    if g:pymode_lint_signs
        call pymode#PlaceSigns()
    endif

    if g:pymode_lint_cwindow
        call pymode#QuickfixOpen(0, g:pymode_lint_hold, g:pymode_lint_maxheight, g:pymode_lint_minheight, g:pymode_lint_jump)
    endif

    if !len(g:qf_list)
        call pymode#WideMessage('Code checking is completed. No errors found.')
    endif

endfunction


fun! pymode#lint#Toggle() "{{{
    let g:pymode_lint = g:pymode_lint ? 0 : 1
    call pymode#lint#toggle_win(g:pymode_lint, "Pymode lint")
endfunction "}}}


fun! pymode#lint#ToggleWindow() "{{{
    let g:pymode_lint_cwindow = g:pymode_lint_cwindow ? 0 : 1
    call pymode#lint#toggle_win(g:pymode_lint_cwindow, "Pymode lint cwindow")
endfunction "}}}


fun! pymode#lint#ToggleChecker() "{{{
    let g:pymode_lint_checker = g:pymode_lint_checker == "pylint" ? "pyflakes" : "pylint"
    echomsg "Pymode lint checker: " . g:pymode_lint_checker
endfunction "}}}


fun! pymode#lint#toggle_win(toggle, msg) "{{{
    if a:toggle
        echomsg a:msg." enabled"
        botright cwindow
        if &buftype == "quickfix"
            wincmd p
        endif
    else
        echomsg a:msg." disabled"
        cclose
    endif
endfunction "}}}


fun! pymode#lint#show_errormessage() "{{{
    if g:pymode_lint_buffer != bufnr('%')
        return 0
    endif
    let errors = getqflist()
    if !len(errors)
        return
    endif
    let [_, line, _, _] = getpos(".")
    for e in errors
        if e['lnum'] == line
            call pymode#WideMessage(e['text'])
        else
            echo
        endif
    endfor
endfunction " }}}


fun! pymode#lint#Auto() "{{{
    if &modifiable && &modified
        try
            write
        catch /E212/
            echohl Error | echo "File modified and I can't save it. Cancel operation." | echohl None
            return 0
        endtry
    endif
    py auto.fix_current_file()
    cclose
    edit
endfunction "}}}
