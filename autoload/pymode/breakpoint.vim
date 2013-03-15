fun! pymode#breakpoint#Set(lnum) "{{{
    let line = getline(a:lnum)
    if strridx(line, g:pymode_breakpoint_cmd) != -1
        normal dd
    else
        let plnum = prevnonblank(a:lnum)
        call append(line('.')-1, repeat(' ', indent(plnum)).g:pymode_breakpoint_cmd)
        normal k
    endif

    " Save file
    if &modifiable && &modified | noautocmd write | endif	

endfunction "}}}
