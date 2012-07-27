fun! pymode#queue#Poll() "{{{
    py from pymode import queue
    py queue.check_task()
    call feedkeys("\<Right>\<Left>", 't')
endfunction "}}}
