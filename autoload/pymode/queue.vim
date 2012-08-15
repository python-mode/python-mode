fun! pymode#queue#Poll() "{{{

    " Check current tasks
    py queue.check_task()

    " Update interval
    if mode() == 'i'
        let p = getpos('.')
        silent exe 'call feedkeys("\<Up>\<Down>", "n")'
        call setpos('.', p)
    else
        call feedkeys("f\e", "n")
    endif

endfunction "}}}
