PymodePython from pymode.lint import code_check

fun! pymode#lint#auto() "{{{
    if !pymode#save()
        return 0
    endif
    PymodePython from pymode import auto
    PymodePython auto()
    cclose
    edit
    call pymode#wide_message("AutoPep8 done.")
endfunction "}}}


fun! pymode#lint#show_errormessage() "{{{
    if empty(b:pymode_errors)
        return
    endif

    let l = line('.')
    if l == b:pymode_error_line
        return
    endif
    let b:pymode_error_line = l
    if has_key(b:pymode_errors, l)
        call pymode#wide_message(b:pymode_errors[l])
    else
        echo
    endif
endfunction "}}}


fun! pymode#lint#toggle() "{{{
    let g:pymode_lint = g:pymode_lint ? 0 : 1
    if g:pymode_lint
        call pymode#wide_message("Code checking is enabled.")
    else
        call pymode#wide_message("Code checking is disabled.")
    end
endfunction "}}}

fun! pymode#lint#check() "{{{
    " DESC: Run checkers on current file.
    "
    if !g:pymode_lint | return | endif

    let b:pymode_errors = {}

    if !pymode#save()
        return 0
    endif

    call pymode#wide_message('Code checking is running ...')

    PymodePython code_check()

    let errors = getqflist()
    if empty(errors)
        call pymode#wide_message('Code checking is completed. No errors found.')
    endif

    if g:pymode_lint_cwindow
        call pymode#quickfix_open(0, g:pymode_quickfix_maxheight, g:pymode_quickfix_minheight, 0)
    endif

    if g:pymode_lint_signs
        for item in b:pymode_signs
            execute printf('sign unplace %d buffer=%d', item.lnum, item.bufnr)
        endfor
        let b:pymode_lint_signs = []
        for item in filter(errors, 'v:val.bufnr != ""')
            call add(b:pymode_signs, item)
            execute printf('sign place %d line=%d name=%s buffer=%d', item.lnum, item.lnum, "Pymode".item.type, item.bufnr)
        endfor
    endif

    for item in errors
        let b:pymode_errors[item.lnum] = item.text
    endfor

    let b:pymode_error_line = -1
    call pymode#lint#show_errormessage()
    call pymode#wide_message('Found errors and warnings: ' . len(errors))

endfunction " }}}

fun! pymode#lint#tick_queue() "{{{

    python import time
    python print time.time()

    if mode() == 'i'
        if col('.') == 1
            call feedkeys("\<Right>\<Left>", "n")
        else
            call feedkeys("\<Left>\<Right>", "n")
        endif
    else
        call feedkeys("f\e", "n")
    endif
endfunction "}}}

fun! pymode#lint#stop() "{{{
    au! pymode CursorHold <buffer>
endfunction

fun! pymode#lint#start() "{{{
    au! pymode CursorHold <buffer> call pymode#lint#tick_queue()
    call pymode#lint#tick_queue()
endfunction
