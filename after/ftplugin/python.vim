" Fix omnifunc
if g:pymode && g:pymode_rope && g:pymode_rope_vim_completion
    setlocal omnifunc=RopeOmni
endif

" Motion {{{

    if !pymode#Default('g:pymode_motion', 1) || g:pymode_motion

        nnoremap <buffer> ]]  :<C-U>call pymode#motion#move2('^\(class\\|def\)\s', '')<CR>
        nnoremap <buffer> [[  :<C-U>call pymode#motion#move2('^\(class\\|def\)\s', 'b')<CR>
        nnoremap <buffer> ]m  :<C-U>call pymode#motion#move2('^\s*def\s', '')<CR>
        nnoremap <buffer> [m  :<C-U>call pymode#motion#move2('^\s*def\s', 'b')<CR>

        onoremap <buffer> ]]  :<C-U>call pymode#motion#move2('^\(class\\|def\)\s', '')<CR>
        onoremap <buffer> [[  :<C-U>call pymode#motion#move2('^\(class\\|def\)\s', 'b')<CR>
        onoremap <buffer> ]m  :<C-U>call pymode#motion#move2('^\s*def\s', '')<CR>
        onoremap <buffer> [m  :<C-U>call pymode#motion#move2('^\s*def\s', 'b')<CR>

        vnoremap <buffer> ]]  :<C-U>call pymode#motion#vmove('^\(class\\|def\)\s', '')<CR>
        vnoremap <buffer> [[  :<C-U>call pymode#motion#vmove('^\(class\\|def\)\s', 'b')<CR>
        vnoremap <buffer> ]m  :<C-U>call pymode#motion#vmove('^\s*def\s', '')<CR>
        vnoremap <buffer> [m  :<C-U>call pymode#motion#vmove('^\s*def\s', 'b')<CR>

        onoremap <buffer> c  :<C-U>call pymode#motion#select('^\s*class\s', 0)<CR>
        onoremap <buffer> ac :<C-U>call pymode#motion#select('^\s*class\s', 0)<CR>
        onoremap <buffer> ic :<C-U>call pymode#motion#select('^\s*class\s', 1)<CR>
        vnoremap <buffer> ac :<C-U>call pymode#motion#select('^\s*class\s', 0)<CR>
        vnoremap <buffer> ic :<C-U>call pymode#motion#select('^\s*class\s', 1)<CR>

        onoremap <buffer> m  :<C-U>call pymode#motion#select('^\s*def\s', 0)<CR>
        onoremap <buffer> am :<C-U>call pymode#motion#select('^\s*def\s', 0)<CR>
        onoremap <buffer> im :<C-U>call pymode#motion#select('^\s*def\s', 1)<CR>
        vnoremap <buffer> am :<C-U>call pymode#motion#select('^\s*def\s', 0)<CR>
        vnoremap <buffer> im :<C-U>call pymode#motion#select('^\s*def\s', 1)<CR>

    endif

" }}}
