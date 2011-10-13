" DESC: Set scriptname
let g:scriptname = expand("<sfile>:t")

" OPTION: g:pymode_breakpoint -- bool. Breakpoints enabled
call helpers#SafeVar("g:pymode_breakpoint", 1)

" OPTION: g:pymode_breakpoint_key -- string. Key for set/unset breakpoint.
call helpers#SafeVar("g:pymode_breakpoint_key", "<leader>b")

" DESC: Disable script loading
if helpers#SafeVar("b:breakpoint", 1) || g:pymode_breakpoint == 0
    finish
endif

" DESC: Set or unset breakpoint
" ARGS: lnum -- int, number of current line
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

" DESC: Set keys
exe "nnoremap <silent> <buffer> " g:pymode_breakpoint_key ":call <SID>:BreakPoint(line('.'))<CR>"
