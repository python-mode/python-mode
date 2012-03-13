" Python-mode motion functions


fun! pymode#motion#move(pattern, flags, ...) "{{{
    let cnt = v:count1 - 1
    let [line, column] = searchpos(a:pattern, a:flags . 'sW')
    let indent = indent(line)
    while cnt && line
        let [line, column] = searchpos(a:pattern, a:flags . 'W')
        if indent(line) == indent
            let cnt = cnt - 1
        endif
    endwhile
    return [line, column]
endfunction "}}}


fun! pymode#motion#vmove(pattern, flags) range "{{{
    call cursor(a:lastline, 0)
    let end = pymode#motion#move(a:pattern, a:flags)
    call cursor(a:firstline, 0)
    normal! v
    call cursor(end)
endfunction "}}} 


fun! pymode#motion#pos_le(pos1, pos2) "{{{
    return ((a:pos1[0] < a:pos2[0]) || (a:pos1[0] == a:pos2[0] && a:pos1[1] <= a:pos2[1]))
endfunction "}}}


fun! pymode#motion#select(pattern, inner) "{{{
    let cnt = v:count1 - 1
    let orig = getpos('.')[1:2]
    let snum = pymode#BlockStart(orig[0], a:pattern)
    if getline(snum) !~ a:pattern
        return 0
    endif
    let enum = pymode#BlockEnd(snum, indent(snum))
    while cnt
        let lnum = search(a:pattern, 'nW')
        if lnum
            let enum = pymode#BlockEnd(lnum, indent(lnum))
            call cursor(enum, 1)
        endif
        let cnt = cnt - 1
    endwhile
    if pymode#motion#pos_le([snum, 0], orig) && pymode#motion#pos_le(orig, [enum, 1])
        if a:inner
            let snum = snum + 1
            let enum = prevnonblank(enum)
        endif

        call cursor(snum, 1)
        normal! v
        call cursor(enum, len(getline(enum)))
    endif
endfunction "}}}


" vim: fdm=marker:fdl=0
