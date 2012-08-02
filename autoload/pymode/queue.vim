fun! pymode#queue#Poll() "{{{
    py queue.check_task()
    call feedkeys("\<Up>\<Down>", 't')
endfunction "}}}
