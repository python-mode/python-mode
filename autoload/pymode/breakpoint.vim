fun! pymode#breakpoint#Set(lnum) "{{{
    let line = getline(a:lnum)
    if strridx(line, g:pymode_breakpoint_cmd) != -1
        normal dd
    else
        let plnum = prevnonblank(a:lnum)
        call append(line('.')-1, repeat(' ', indent(plnum)).g:pymode_breakpoint_cmd)
        normal k
    endif

    " Disable lint
    let pymode_lint = g:pymode_lint
    let g:pymode_lint = 0

    " Save file
    if &modifiable && &modified | write | endif	

    let g:pymode_lint = pymode_lint

endfunction "}}}
