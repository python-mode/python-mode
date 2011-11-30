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


fun! pymode#motion#move(pattern, flags) "{{{
    let i = v:count1
    while i > 0
        let result = searchpos(a:pattern, a:flags.'W')
        let i = i - 1
    endwhile
    return result
endfunction "}}} 


fun! pymode#motion#vmove(pattern, flags) "{{{
    let end = pymode#motion#move(a:pattern, a:flags)
    normal! gv
    call cursor(end)
endfunction "}}} 


fun! pymode#motion#pos_le(pos1, pos2) "{{{
    return ((a:pos1[0] < a:pos2[0]) || (a:pos1[0] == a:pos2[0] && a:pos1[1] <= a:pos2[1]))
endfunction "}}}


fun! pymode#motion#select(pattern, inner) "{{{
    let orig = getpos('.')[1:2]
    let start = pymode#motion#move(a:pattern, 'bW')
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
