" Fix omnifunc
if g:pymode && g:pymode_rope && g:pymode_rope_vim_completion
    setlocal omnifunc=RopeOmni
endif

" Motion {{{

    if !pymode#Default('g:pymode_motion', 1) || g:pymode_motion

        nnoremap <buffer> ]] :call pymode#motion#move('^\(class\\|def\)\s', '')<CR>
        nnoremap <buffer> [[ :call pymode#motion#move('^\(class\\|def\)\s', 'b')<CR>
        nnoremap <buffer> ]m :call pymode#motion#move('^\s*\(class\\|def\)\s', '')<CR>
        nnoremap <buffer> [m :call pymode#motion#move('^\s*\(class\\|def\)\s', 'b')<CR>
        onoremap <buffer> ]] :call pymode#motion#move('^\(class\\|def\)\s', '')<CR>
        onoremap <buffer> [[ :call pymode#motion#move('^\(class\\|def\)\s', 'b')<CR>
        onoremap <buffer> ]m :call pymode#motion#move('^\s*\(class\\|def\)\s', '')<CR>
        onoremap <buffer> [m :call pymode#motion#move('^\s*\(class\\|def\)\s', 'b')<CR>
        vnoremap <buffer> ]] :call pymode#motion#vmove('^\(class\\|def\)\s', '')<CR>
        vnoremap <buffer> [[ :call pymode#motion#vmove('^\(class\\|def\)\s', 'b')<CR>
        vnoremap <buffer> ]m :call pymode#motion#vmove('^\s*\(class\\|def\)\s', '')<CR>
        vnoremap <buffer> [m :call pymode#motion#vmove('^\s*\(class\\|def\)\s', 'b')<CR>

        nnoremap <buffer> vac :call pymode#motion#select('^\s*\(class\)\s', 0)<CR>
        nnoremap <buffer> vic :call pymode#motion#select('^\s*\(class\)\s', 1)<CR>
        nnoremap <buffer> vam :call pymode#motion#select('^\s*\(def\)\s', 0)<CR>
        nnoremap <buffer> vim :call pymode#motion#select('^\s*\(def\)\s', 1)<CR>
        onoremap <buffer> am :call pymode#motion#select('^\s*\(def\)\s', 0)<CR>
        onoremap <buffer> im :call pymode#motion#select('^\s*\(def\)\s', 1)<CR>
        onoremap <buffer> ac :call pymode#motion#select('^\s*\(class\)\s', 0)<CR>
        onoremap <buffer> ic :call pymode#motion#select('^\s*\(class\)\s', 1)<CR>

    endif

" }}}
