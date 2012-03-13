fun! pymode#lint#Check()

    if !g:pymode_lint | return | endif

    let b:errors = {}

    if &modifiable && &modified
        try
            write
        catch /E212/
            echohl Error | echo "File modified and I can't save it. Cancel code checking." | echohl None
            return 0
        endtry
    endif	

    py check_file()

    if g:qf_list != b:qf_list

        call setqflist(b:qf_list, 'r')

        let g:qf_list = b:qf_list

        if g:pymode_lint_message
            for v in b:qf_list
                let b:errors[v['lnum']] = v['text']
            endfor
            call pymode#lint#show_errormessage()
        endif

        if g:pymode_lint_cwindow
            call pymode#QuickfixOpen(0, g:pymode_lint_hold, g:pymode_lint_maxheight, g:pymode_lint_minheight, g:pymode_lint_jump)
        endif

    endif

    if g:pymode_lint_signs
        call pymode#PlaceSigns()
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
    if !len(b:errors) | return | endif
    let cursor = getpos(".")
    if has_key(b:errors, l:cursor[1])
        call pymode#WideMessage(b:errors[l:cursor[1]])
        let b:show_message = 1
    else
        let b:show_message = 0
        echo
    endif
endfunction " }}}
