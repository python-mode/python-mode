PymodePython from pymode.lint import code_check

call pymode#tools#signs#init()
call pymode#tools#loclist#init()


fun! pymode#lint#auto() "{{{
    if ! pymode#save()
        return 0
    endif
    PymodePython from pymode import auto
    PymodePython auto()
    cclose
    call g:PymodeSigns.clear()
    edit
    call pymode#wide_message("AutoPep8 done.")
endfunction "}}}


fun! pymode#lint#show_errormessage() "{{{
    let loclist = g:PymodeLocList.current()
    if loclist.is_empty()
        return
    endif

    let l = line('.')
    if l == b:pymode_error_line
        return
    endif
    let b:pymode_error_line = l
    if has_key(loclist._messages, l)
        call pymode#wide_message(loclist._messages[l])
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
    endif
endfunction "}}}


fun! pymode#lint#check() "{{{
    " DESC: Run checkers on current file.
    "
    let loclist = g:PymodeLocList.current()

    let b:pymode_error_line = -1

    call loclist.clear()

    call pymode#wide_message('Code checking is running ...')

    PymodePython code_check()

    if loclist.is_empty()
        call pymode#wide_message('Code checking is completed. No errors found.')
        call g:PymodeSigns.refresh(loclist)
        call loclist.show()
        return
    endif

    call g:PymodeSigns.refresh(loclist)

    call loclist.show()

    call pymode#lint#show_errormessage()
    call pymode#wide_message('Found ' . loclist.num_errors() . ' error(s) and ' . loclist.num_warnings() . ' warning(s)')

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
endfunction "}}}


fun! pymode#lint#start() "{{{
    au! pymode CursorHold <buffer> call pymode#lint#tick_queue()
    call pymode#lint#tick_queue()
endfunction "}}}
