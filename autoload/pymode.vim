fun! pymode#Default(name, default) "{{{
    if !exists(a:name)
        let {a:name} = a:default
        return 0
    endif
    return 1
endfunction "}}}

fun! pymode#QuickfixOpen(onlyRecognized, holdCursor, maxHeight, minHeight, jumpError) "{{{
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
    sign unplace *
    for item in filter(getqflist(), 'v:val.bufnr != ""')
        execute printf('silent! sign place 1 line=%d name=%s buffer=%d', item.lnum, item.type, item.bufnr)
    endfor
endfunction "}}}


fun! pymode#CheckProgram(name, append) "{{{
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
    pclose | botright 8new
    setlocal buftype=nofile bufhidden=delete noswapfile nowrap previewwindow
    redraw
endfunction "}}}

fun! pymode#ShowStr(str) "{{{
    call pymode#TempBuffer()
    put! =a:str
    redraw
    normal gg
    wincmd p
endfunction "}}}

fun! pymode#ShowCommand(cmd) "{{{
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


" DESC: Show wide message
fun! pymode#WideMessage(msg) "{{{
    let x=&ruler | let y=&showcmd
    set noruler noshowcmd
    redraw
    echo strpart(a:msg, 0, &columns-1)
    let &ruler=x | let &showcmd=y
endfunction "}}}
