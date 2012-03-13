" Fix omnifunc
if g:pymode && g:pymode_rope && g:pymode_rope_vim_completion
    setlocal omnifunc=RopeOmni
endif

" Motion {{{

    if !pymode#Default('g:pymode_motion', 1) || g:pymode_motion

        nnoremap <buffer> ]]  :<C-U>call pymode#motion#move('^\(class\\|def\)\s', '')<CR>
        nnoremap <buffer> [[  :<C-U>call pymode#motion#move('^\(class\\|def\)\s', 'b')<CR>
        nnoremap <buffer> ]C  :<C-U>call pymode#motion#move('^\(class\\|def\)\s', '')<CR>
        nnoremap <buffer> [C  :<C-U>call pymode#motion#move('^\(class\\|def\)\s', 'b')<CR>
        nnoremap <buffer> ]M  :<C-U>call pymode#motion#move('^\s*def\s', '')<CR>
        nnoremap <buffer> [M  :<C-U>call pymode#motion#move('^\s*def\s', 'b')<CR>

        onoremap <buffer> ]]  :<C-U>call pymode#motion#move('^\(class\\|def\)\s', '')<CR>
        onoremap <buffer> [[  :<C-U>call pymode#motion#move('^\(class\\|def\)\s', 'b')<CR>
        onoremap <buffer> ]C  :<C-U>call pymode#motion#move('^\(class\\|def\)\s', '')<CR>
        onoremap <buffer> [C  :<C-U>call pymode#motion#move('^\(class\\|def\)\s', 'b')<CR>
        onoremap <buffer> ]M  :<C-U>call pymode#motion#move('^\s*def\s', '')<CR>
        onoremap <buffer> [M  :<C-U>call pymode#motion#move('^\s*def\s', 'b')<CR>

        vnoremap <buffer> ]]  :call pymode#motion#vmove('^\(class\\|def\)\s', '')<CR>
        vnoremap <buffer> [[  :call pymode#motion#vmove('^\(class\\|def\)\s', 'b')<CR>
        vnoremap <buffer> ]M  :call pymode#motion#vmove('^\s*def\s', '')<CR>
        vnoremap <buffer> [M  :call pymode#motion#vmove('^\s*def\s', 'b')<CR>

        onoremap <buffer> C  :<C-U>call pymode#motion#select('^\s*class\s', 0)<CR>
        onoremap <buffer> aC :<C-U>call pymode#motion#select('^\s*class\s', 0)<CR>
        onoremap <buffer> iC :<C-U>call pymode#motion#select('^\s*class\s', 1)<CR>
        vnoremap <buffer> aC :<C-U>call pymode#motion#select('^\s*class\s', 0)<CR>
        vnoremap <buffer> iC :<C-U>call pymode#motion#select('^\s*class\s', 1)<CR>

        onoremap <buffer> M  :<C-U>call pymode#motion#select('^\s*def\s', 0)<CR>
        onoremap <buffer> aM :<C-U>call pymode#motion#select('^\s*def\s', 0)<CR>
        onoremap <buffer> iM :<C-U>call pymode#motion#select('^\s*def\s', 1)<CR>
        vnoremap <buffer> aM :<C-U>call pymode#motion#select('^\s*def\s', 0)<CR>
        vnoremap <buffer> iM :<C-U>call pymode#motion#select('^\s*def\s', 1)<CR>

    endif

" }}}
