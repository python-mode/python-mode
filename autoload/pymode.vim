" Python-mode base functions


fun! pymode#Default(name, default) "{{{
    " DESC: Set default value if it not exists
    "
    if !exists(a:name)
        let {a:name} = a:default
        return 0
    endif
    return 1
endfunction "}}}


fun! pymode#QuickfixOpen(onlyRecognized, holdCursor, maxHeight, minHeight, jumpError) "{{{
    " DESC: Open quickfix window
    "
    let numErrors = len(filter(getqflist(), 'v:val.valid'))
    let numOthers = len(getqflist()) - numErrors
    if numErrors > 0 || (!a:onlyRecognized && numOthers > 0)
        botright copen
        exe max([min([line("$"), a:maxHeight]), a:minHeight]) . "wincmd _"
        if a:jumpError
            cc
        elseif a:holdCursor
            wincmd p
        endif
    else
        cclose
    endif
    redraw
    if numOthers > 0
        echo printf('Quickfix: %d(+%d)', numErrors, numOthers)
    else
        echo printf('Quickfix: %d', numErrors)
    endif
endfunction "}}}


fun! pymode#PlaceSigns() "{{{
    " DESC: Place error signs
    "
    sign unplace *
    for item in filter(getqflist(), 'v:val.bufnr != ""')
        execute printf('silent! sign place 1 line=%d name=%s buffer=%d', item.lnum, item.type, item.bufnr)
    endfor
endfunction "}}}


fun! pymode#CheckProgram(name, append) "{{{
    " DESC: Check program is executable or redifined by user.
    "
    let name = 'g:' . a:name
    if pymode#Default(name, a:name)
        return 1
    endif
    if !executable(eval(l:name))
        echoerr "Can't find '".eval(name)."'. Please set ".name .", or extend $PATH, ".a:append
        return 0
    endif
    return 1
endfunction "}}}


fun! pymode#TempBuffer() "{{{
    " DESC: Open temp buffer.
    "
    pclose | botright 8new
    setlocal buftype=nofile bufhidden=delete noswapfile nowrap previewwindow
    redraw
endfunction "}}}


fun! pymode#ShowStr(str) "{{{
    " DESC: Open temp buffer with `str`.
    "
    let g:pymode_curbuf = bufnr("%")
    call pymode#TempBuffer()
    put! =a:str
    redraw
    normal gg 
    wincmd p
endfunction "}}}


fun! pymode#ShowCommand(cmd) "{{{
    " DESC: Run command and open temp buffer with result
    "
    call pymode#TempBuffer()
    try
        silent exec 'r!' . a:cmd
    catch /.*/
        close
        echoerr 'Command fail: '.a:cmd
    endtry
    redraw
    normal gg
    wincmd p
endfunction "}}}


fun! pymode#WideMessage(msg) "{{{
    " DESC: Show wide message

    let x=&ruler | let y=&showcmd
    set noruler noshowcmd
    redraw
    echo strpart(a:msg, 0, &columns-1)
    let &ruler=x | let &showcmd=y
endfunction "}}}


fun! pymode#BlockStart(lnum, ...) "{{{
    let pattern = a:0 ? a:1 : '^\s*\(@\|class\s.*:\|def\s\)'
    let lnum = a:lnum + 1
    let indent = 100
    while lnum
        let lnum = prevnonblank(lnum - 1)
        let test = indent(lnum)
        let line = getline(lnum)
        if line =~ '^\s*#' " Skip comments
            continue
        elseif !test " Zero-level regular line
            return lnum
        elseif test >= indent " Skip deeper or equal lines
            continue
        " Indent is strictly less at this point: check for def/class
        elseif line =~ pattern && line !~ '^\s*@'
            return lnum
        endif
        let indent = indent(lnum)
    endwhile
    return 0
endfunction "}}}


fun! pymode#BlockEnd(lnum, ...) "{{{
    let indent = a:0 ? a:1 : indent(a:lnum)
    let lnum = a:lnum
    while lnum
        let lnum = nextnonblank(lnum + 1)
        if getline(lnum) =~ '^\s*#' | continue
        elseif lnum && indent(lnum) <= indent
            return lnum - 1
        endif
    endwhile
    return line('$')
endfunction "}}}


" vim: fdm=marker:fdl=0
