" Check indentation level on motion
" dC dM

fun! pymode#motion#block(lnum) "{{{
    let start = indent(a:lnum)
    let num = a:lnum
    while num
        let num = nextnonblank(num + 1)
        if num && indent(num) <= start
            return num - 1
        endif
    endwhile
    return line('$')
endfunction "}}}


fun! pymode#motion#move2(pattern, flags, ...) "{{{
    normal! m'
    let cnt = v:count1 - 1
    let [line, column] = searchpos(a:pattern, a:flags . 'W')
    let indent = indent(line)

    while l:cnt && l:line
        let [line, column] = searchpos(a:pattern, a:flags . 'W')
        if indent(line) == l:indent
            let cnt = l:cnt - 1
        endif
    endwhile

    return [line, column]

endfunction "}}}


fun! pymode#motion#vmove(pattern, flags) "{{{
    let end = pymode#motion#move2(a:pattern, a:flags)
    normal! gv
    call cursor(end)
endfunction "}}} 


fun! pymode#motion#pos_le(pos1, pos2) "{{{
    return ((a:pos1[0] < a:pos2[0]) || (a:pos1[0] == a:pos2[0] && a:pos1[1] <= a:pos2[1]))
endfunction "}}}


fun! pymode#motion#select(pattern, inner) "{{{
    let orig = getpos('.')[1:2]
    let start = pymode#motion#move2(a:pattern, 'cb')
    let eline = pymode#motion#block(start[0])
    let end = [eline, len(getline(eline))]
    call cursor(orig)

    if pymode#motion#pos_le(start, orig) && pymode#motion#pos_le(orig, end)
        if a:inner
            let start = [start[0] + 1, start[1]]
            let eline = prevnonblank(end[0])
            let end = [eline, len(getline(eline))] 
        endif
        normal! v
        call cursor(start)
        normal! o
        call cursor(end)
    endif
endfunction "}}}
