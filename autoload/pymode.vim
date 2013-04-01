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


fun! pymode#Option(name) "{{{

    let name = 'b:pymode_' . a:name
    if exists(name)
        return eval(name)
    endif

    let name = 'g:pymode_' . a:name
    return eval(name)

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
        elseif !a:holdCursor
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


fun! pymode#PlaceSigns(bnum) "{{{
    " DESC: Place error signs
    "
    if has('signs')
        call pymode#Default('b:pymode_signs', [])

        for item in b:pymode_signs
            execute printf('sign unplace %d buffer=%d', item.lnum, item.bufnr)
        endfor
        let b:pymode_signs = []

        if !pymode#Default("g:pymode_lint_signs_always_visible", 0) || g:pymode_lint_signs_always_visible
            call RopeShowSignsRulerIfNeeded()
        endif

        for item in filter(getqflist(), 'v:val.bufnr != ""')
            call add(b:pymode_signs, item)
            execute printf('sign place %d line=%d name=%s buffer=%d', item.lnum, item.lnum, "Pymode".item.type, item.bufnr)
        endfor

    endif
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
    wincmd p
    redraw
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
    echohl Debug | echo strpart(a:msg, 0, &columns-1) | echohl none
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


fun! pymode#Modeline() "{{{
    let modeline = getline(prevnonblank('$'))
    if modeline =~ '^#\s\+pymode:'
        for ex in split(modeline, ':')[1:]
            let [name, value] = split(ex, '=')
            let {'b:pymode_'.name} = value
        endfor
    endif
    au BufRead <buffer> call pymode#Modeline()
endfunction "}}}


fun! pymode#TrimWhiteSpace() "{{{
    let cursor_pos = getpos('.')
    silent! %s/\s\+$//
    call setpos('.', cursor_pos)
endfunction "}}}


" vim: fdm=marker:fdl=0
