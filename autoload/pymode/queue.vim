fun! pymode#queue#Poll() "{{{

    " Check current tasks
    py queue.check_task()

    " Update interval
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
