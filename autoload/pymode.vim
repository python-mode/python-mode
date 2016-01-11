" Pymode core functions

" DESC: Check variable and set default value if it not exists
fun! pymode#default(name, default) "{{{
    if !exists(a:name)
        let {a:name} = a:default
        return 0
    endif
    return 1
endfunction "}}}

" DESC: Import python libs
fun! pymode#init(plugin_root, paths) "{{{

    PymodePython import sys, vim
    PymodePython sys.path.insert(0, vim.eval('a:plugin_root'))
    PymodePython sys.path = vim.eval('a:paths') + sys.path

endfunction "}}}

" DESC: Show wide message
fun! pymode#wide_message(msg) "{{{
    let x=&ruler | let y=&showcmd
    set noruler noshowcmd
    redraw
    echohl Debug | echo strpart("[Pymode] " . a:msg, 0, &columns-1) | echohl none
    let &ruler=x | let &showcmd=y
endfunction "}}}

" DESC: Show error
fun! pymode#error(msg) "{{{
    execute "normal \<Esc>"
    echohl ErrorMsg
    echomsg "[Pymode]: error: " . a:msg
    echohl None
endfunction "}}}

" DESC: Open quickfix window
fun! pymode#quickfix_open(onlyRecognized, maxHeight, minHeight, jumpError) "{{{
    let numErrors = len(filter(getqflist(), 'v:val.valid'))
    let numOthers = len(getqflist()) - numErrors
    if numErrors > 0 || (!a:onlyRecognized && numOthers > 0)
        let num = winnr()
        botright copen
        exe max([min([line("$"), a:maxHeight]), a:minHeight]) . "wincmd _"
        if a:jumpError
            cc
        elseif num != winnr()
            wincmd p
        endif
    else
        cclose
    endif
    redraw
    if numOthers > 0
        call pymode#wide_message(printf('Quickfix: %d(+%d)', numErrors, numOthers))
    elseif numErrors > 0
        call pymode#wide_message(printf('Quickfix: %d', numErrors))
    endif
endfunction "}}}

" DESC: Open temp buffer.
fun! pymode#tempbuffer_open(name) "{{{
    pclose
    exe "botright 8new " . a:name
    setlocal buftype=nofile bufhidden=delete noswapfile nowrap previewwindow
    redraw
endfunction "}}}

" DESC: Remove unused whitespaces
fun! pymode#trim_whitespaces() "{{{
    if g:pymode_trim_whitespaces
        let cursor_pos = getpos('.')
        silent! %s/\s\+$//
        call setpos('.', cursor_pos)
    endif
endfunction "}}}


fun! pymode#save() "{{{
    if &modifiable && &modified
        try
            noautocmd write
        catch /E212/
            call pymode#error("File modified and I can't save it. Please save it manually.")
            return 0
        endtry
    endif
    return expand('%') != ''
endfunction "}}}

fun! pymode#reload_buf_by_nr(nr) "{{{
    let cur = bufnr("")
    try
        exe "buffer " . a:nr
    catch /E86/
        return
    endtry
    exe "e!"
    exe "buffer " . cur
endfunction "}}}

fun! pymode#buffer_pre_write() "{{{
    let b:pymode_modified = &modified
endfunction "}}}

fun! pymode#buffer_post_write() "{{{
    if g:pymode_rope
        if g:pymode_rope_regenerate_on_write && b:pymode_modified
            call pymode#debug('regenerate')
            call pymode#rope#regenerate()
        endif
    endif
    if g:pymode_lint
        if g:pymode_lint_unmodified || (g:pymode_lint_on_write && b:pymode_modified)
            call pymode#debug('check code')
            call pymode#lint#check()
        endif
    endif
endfunction "}}}

fun! pymode#debug(msg) "{{{
    if g:pymode_debug
        let g:pymode_debug += 1
        echom string(g:pymode_debug) . ': ' . string(a:msg)
    endif
endfunction "}}}

fun! pymode#quit() "{{{
    augroup pymode
        au! * <buffer>
    augroup END
endfunction "}}}
