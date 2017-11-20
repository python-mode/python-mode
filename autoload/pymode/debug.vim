" Set debugging functions.

" DESC: Get debug information about pymode problem.
fun! pymode#debug#sysinfo() "{{{
    " OS info. {{{
    let l:os_name = "Unknown"
    if has('win16') || has('win32') || has('win64')
        let l:os_name = "Windows"
    else
        let l:os_name = substitute(system('uname'), "\n", "", "")
    endif
    call pymode#debug("Operating system: " . l:os_name)
    " }}}
    " Loaded scripts info. {{{
    call pymode#debug("Scriptnames:")
    let l:scriptnames_var = execute('scriptnames')
    " }}}
    " Variables info. {{{
    " Drop verbose file temporarily to prevent the 'let' from showing up.
    let l:tmp = &verbosefile
    set verbosefile=
    let l:all_variables = filter(
        \ split(execute('let', 'silent!'), '\n'),
        \ 'v:val =~ "^pymode"')
    let &verbosefile = l:tmp
    " NOTE: echom does not display multiline messages. Thus a for loop is
    " needed.
    call pymode#debug("Pymode variables:")
    for pymodevar in sort(l:all_variables)
        echom pymodevar
    endfor
    " }}}
    " Github commit info. {{{
    " Find in the scriptnames the first occurence of 'python-mode'. Then parse
    " the result outputting its path. This is in turn fed into the git command.
    call pymode#debug("Git commit: ")
    let l:pymode_folder = substitute(
        \ filter(
            \ split(l:scriptnames_var, '\n'),
            \ 'v:val =~ "/python-mode/"')[0],
        \ '\(^\s\+[0-9]\+:\s\+\)\([/~].*python-mode\/\)\(.*\)',
        \ '\2',
        \ '')
    let l:git_head_sha1 = system('git -C ' . expand(l:pymode_folder). ' rev-parse HEAD ' )
    echom join(filter(split(l:git_head_sha1, '\zs'), 'v:val =~? "[0-9A-Fa-f]"'), '')
    " }}}
    call pymode#debug("End of pymode#debug#sysinfo")
endfunction "}}}

" DESC: Define debug folding function.
function! pymode#debug#foldingexpr(lnum) "{{{
    let l:get_folding_result = pymode#folding#foldcase(a:lnum)
    " NOTE: the 'has folding:' expression is special in the pymode#debug.
    call pymode#debug(
        \ 'line ' . a:lnum
        \ . ' has folding: ' . l:get_folding_result['foldlevel']
        \ . ' with foldcase ' . l:get_folding_result['foldcase'])
    return l:get_folding_result['foldlevel']
endfunction
" }}}
