" DESC: Set scriptname
let g:scriptname = expand('<sfile>:t')

" DESC: Set var if not exists
" ARGS: name -- str, variable name
"       value -- variable value
fun! helpers#SafeVar(name, value) "{{{
    if !exists(a:name)
        execute('let ' . a:name . ' = ' . string(a:value))
        return 0
    endif
    return 1
endfunction "}}}


" DESC: Show preview window
" ARGS: output -- str, window content
fun! helpers#ShowPreview(output) "{{{
    redraw | pclose | botright 8new
    setlocal buftype=nofile bufhidden=wipe noswapfile nowrap previewwindow
    put! =a:output
    $del | wincmd p | redraw
endfunction "}}}


" DESC: Run command and show preview window
" ARGS: cmd -- str, shell command
fun! helpers#ShowPreviewCmd(cmd) "{{{
    pclose | botright 8new
    setlocal buftype=nofile bufhidden=wipe noswapfile nowrap previewwindow
    try
        silent exec 'r!' . a:cmd
    catch /.*/
        close
        echoerr 'Command fail'
    endtry
    redraw
    normal gg
    wincmd p
endfunction "}}}


" OPTION: g:MakeSave -- bool, Save buffer before validation.
call helpers#SafeVar('g:MakeSave', 1)

" OPTION: g:MakeCWindow -- bool. Show cwindow
call helpers#SafeVar('g:MakeCWindow', 1)

" OPTION: g:MakeErrorSigns -- bool. Show error signs
call helpers#SafeVar('g:MakeErrorSigns', 1)


" DESC: Validate code
" ARGS: cmd -- str, command for fill quickfix buffer
fun! helpers#Lint(cmd) "{{{
    cclose
    if g:MakeSave && &modifiable && &modified | write | endif	
    silent exec a:cmd
    if g:MakeCWindow | botright cwindow | endif
    if g:MakeErrorSigns | call helpers#PlaceErrorSigns() | endif
endfunction "}}}


" DESC: Place error signs, by quickfix window
fun! helpers#PlaceErrorSigns() "{{{
    sign unplace *
    let l:id = 1
    for item in getqflist()
        if l:item.bufnr != ''
            execute(':silent sign place '.l:id.' name='.l:item.type.' line='.l:item.lnum.' buffer='.l:item.bufnr)
        endif
        let l:id = l:id + 1
    endfor
endfunction "}}}


fun! helpers#CheckProgramm(name) "{{{
    let varname = 'g:' . a:name
    if helpers#SafeVar(varname, a:name)
        return 1
    endif
    if !executable(eval(l:varname))
        echoerr g:scriptname . ": can't find '" . eval(l:varname) . "'. Please set " . l:varname . ", or extend $PATH"
        return 0
    endif
    return 1
endfunction "}}}
