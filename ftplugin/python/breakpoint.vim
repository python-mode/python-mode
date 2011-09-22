if helpers#SafeVar("b:breakpoint", 1)
    finish
endif

fun! <SID>:BreakPoint(lnum) "{{{
    let import = "import ipdb; ipdb.set_trace() ### XXX BREAKPOINT"
    let line = getline(a:lnum)

    if strridx(line, import) != -1
        normal dd
        return 1
    endif

    let plnum = prevnonblank(a:lnum)
    let indent = indent(plnum)

    call append(line('.') - 1, repeat(' ', indent) . import)
    normal k

endfunction "}}}

nnoremap <silent> <buffer> <leader>b :call <SID>:BreakPoint(line('.'))<CR>
