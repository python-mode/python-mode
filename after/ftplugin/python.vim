if !g:pymode
    finish
endif

if g:pymode_motion

    if !&magic
        if g:pymode_warning
            call pymode#error("Pymode motion requires `&magic` option. Enable them or disable g:pymode_motion")
        endif
        finish
    endif

    nnoremap <buffer> ]]  :<C-U>call pymode#motion#move('^<Bslash>(class<Bslash><bar><Bslash>%(async<Bslash>s<Bslash>+<Bslash>)<Bslash>=def<Bslash>)<Bslash>s', '')<CR>
    nnoremap <buffer> [[  :<C-U>call pymode#motion#move('^<Bslash>(class<Bslash><bar><Bslash>%(async<Bslash>s<Bslash>+<Bslash>)<Bslash>=def<Bslash>)<Bslash>s', 'b')<CR>
    nnoremap <buffer> ]C  :<C-U>call pymode#motion#move('^<Bslash>(class<Bslash><bar><Bslash>%(async<Bslash>s<Bslash>+<Bslash>)<Bslash>=def<Bslash>)<Bslash>s', '')<CR>
    nnoremap <buffer> [C  :<C-U>call pymode#motion#move('^<Bslash>(class<Bslash><bar><Bslash>%(async<Bslash>s<Bslash>+<Bslash>)<Bslash>=def<Bslash>)<Bslash>s', 'b')<CR>
    nnoremap <buffer> ]M  :<C-U>call pymode#motion#move('^<Bslash>s*<Bslash>(async<Bslash>s<Bslash>+<Bslash>)<Bslash>=def<Bslash>s', '')<CR>
    nnoremap <buffer> [M  :<C-U>call pymode#motion#move('^<Bslash>s*<Bslash>(async<Bslash>s<Bslash>+<Bslash>)<Bslash>=def<Bslash>s', 'b')<CR>

    onoremap <buffer> ]]  :<C-U>call pymode#motion#move('^<Bslash>(class<Bslash><bar><Bslash>%(async<Bslash>s<Bslash>+<Bslash>)<Bslash>=def<Bslash>)<Bslash>s', '')<CR>
    onoremap <buffer> [[  :<C-U>call pymode#motion#move('^<Bslash>(class<Bslash><bar><Bslash>%(async<Bslash>s<Bslash>+<Bslash>)<Bslash>=def<Bslash>)<Bslash>s', 'b')<CR>
    onoremap <buffer> ]C  :<C-U>call pymode#motion#move('^<Bslash>(class<Bslash><bar><Bslash>%(async<Bslash>s<Bslash>+<Bslash>)<Bslash>=def<Bslash>)<Bslash>s', '')<CR>
    onoremap <buffer> [C  :<C-U>call pymode#motion#move('^<Bslash>(class<Bslash><bar><Bslash>%(async<Bslash>s<Bslash>+<Bslash>)<Bslash>=def<Bslash>)<Bslash>s', 'b')<CR>
    onoremap <buffer> ]M  :<C-U>call pymode#motion#move('^<Bslash>s*<Bslash>(async<Bslash>s<Bslash>+<Bslash>)<Bslash>=def<Bslash>s', '')<CR>
    onoremap <buffer> [M  :<C-U>call pymode#motion#move('^<Bslash>s*<Bslash>(async<Bslash>s<Bslash>+<Bslash>)<Bslash>=def<Bslash>s', 'b')<CR>

    vnoremap <buffer> ]]  :call pymode#motion#vmove('^<Bslash>(class<Bslash><bar><Bslash>%(async<Bslash>s<Bslash>+<Bslash>)<Bslash>=def<Bslash>)<Bslash>s', '')<CR>
    vnoremap <buffer> [[  :call pymode#motion#vmove('^<Bslash>(class<Bslash><bar><Bslash>%(async<Bslash>s<Bslash>+<Bslash>)<Bslash>=def<Bslash>)<Bslash>s', 'b')<CR>
    vnoremap <buffer> ]M  :call pymode#motion#vmove('^<Bslash>s*<Bslash>(async<Bslash>s<Bslash>+<Bslash>)<Bslash>=def<Bslash>s', '')<CR>
    vnoremap <buffer> [M  :call pymode#motion#vmove('^<Bslash>s*<Bslash>(async<Bslash>s<Bslash>+<Bslash>)<Bslash>=def<Bslash>s', 'b')<CR>

    onoremap <buffer> C  :<C-U>call pymode#motion#select('^<Bslash>s*class<Bslash>s', 0)<CR>
    onoremap <buffer> aC :<C-U>call pymode#motion#select('^<Bslash>s*class<Bslash>s', 0)<CR>
    onoremap <buffer> iC :<C-U>call pymode#motion#select('^<Bslash>s*class<Bslash>s', 1)<CR>
    vnoremap <buffer> aC :<C-U>call pymode#motion#select('^<Bslash>s*class<Bslash>s', 0)<CR>
    vnoremap <buffer> iC :<C-U>call pymode#motion#select('^<Bslash>s*class<Bslash>s', 1)<CR>

    onoremap <buffer> M  :<C-U>call pymode#motion#select('^<Bslash>s*<Bslash>(async<Bslash>s<Bslash>+<Bslash>)<Bslash>=def<Bslash>s', 0)<CR>
    onoremap <buffer> aM :<C-U>call pymode#motion#select('^<Bslash>s*<Bslash>(async<Bslash>s<Bslash>+<Bslash>)<Bslash>=def<Bslash>s', 0)<CR>
    onoremap <buffer> iM :<C-U>call pymode#motion#select('^<Bslash>s*<Bslash>(async<Bslash>s<Bslash>+<Bslash>)<Bslash>=def<Bslash>s', 1)<CR>
    vnoremap <buffer> aM :<C-U>call pymode#motion#select('^<Bslash>s*<Bslash>(async<Bslash>s<Bslash>+<Bslash>)<Bslash>=def<Bslash>s', 0)<CR>
    vnoremap <buffer> iM :<C-U>call pymode#motion#select('^<Bslash>s*<Bslash>(async<Bslash>s<Bslash>+<Bslash>)<Bslash>=def<Bslash>s', 1)<CR>

endif

if g:pymode_rope && g:pymode_rope_completion

    setlocal omnifunc=pymode#rope#completions

    if g:pymode_rope_completion_bind != ""
        exe "inoremap <silent> <buffer> " . g:pymode_rope_completion_bind . " <C-R>=pymode#rope#complete(0)<CR>"
        if tolower(g:pymode_rope_completion_bind) == '<c-space>'
            exe "inoremap <silent> <buffer> <Nul> <C-R>=pymode#rope#complete(0)<CR>"
        endif
    endif

endif
