" OPTION: g:pymode_breakpoint -- bool. Breakpoints enabled
call helpers#SafeVar("g:pymode_breakpoint", 1)

" DESC: Disable script loading
if ! g:pymode_breakpoint
    finish
endif

" OPTION: g:pymode_breakpoint_key -- string. Key for set/unset breakpoint.
call helpers#SafeVar("g:pymode_breakpoint_key", "<leader>b")

" DESC: Set or unset breakpoint
" ARGS: lnum -- int, number of current line
fun! pymode_breakpoint#Set(lnum) "{{{
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
