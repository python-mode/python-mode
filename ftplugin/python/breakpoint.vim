if helpers#SafeVar("b:breakpoint", 1)
    finish
endif

fun! <SID>:BreakPoint() "{{{
    let import = "import ipdb; ipdb.set_trace() ### XXX BREAKPOINT"
    let line = getline('.')
    let plinr = line('.') - 1
    let pline = getline(plinr)
    let indent = indent('.')
    let in = ''

    if strridx(line, import) != -1
        normal dd
        return 1
    endif

    while pline == '' && indent == 0
        let plinr = plinr - 1
        let pline = getline(plinr)
        let indent = indent(plinr)
    endwhile

    while indent > 0
        let in = in . ' '
        let indent -= 1
    endwhile

    call append(line('.') - 1, in . import)
    normal k

endfunction "}}}

nnoremap <silent> <buffer> <leader>b :call <SID>:BreakPoint()<CR>
