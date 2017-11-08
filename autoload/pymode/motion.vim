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
    let snum = s:BlockStart(orig[0], a:pattern)
    if getline(snum) !~ a:pattern
        return 0
    endif
    let enum = s:BlockEnd(snum, indent(snum))
    while cnt
        let lnum = search(a:pattern, 'nW')
        if lnum
            let enum = s:BlockEnd(lnum, indent(lnum))
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


fun! s:BlockStart(lnum, ...) "{{{
    let pattern = a:0 ? a:1 : '^\s*\(@\|class\s.*:\|def\s\)'
    let lnum = a:lnum + 1
    let indent = 100
    while lnum
        let lnum = prevnonblank(lnum - 1)
        let test = indent(lnum)
        let line = getline(lnum)
        if line =~ '^\s*#' " Skip comments
            continue
        elseif !test " Zero-level regular line
            return lnum
        elseif test >= indent " Skip deeper or equal lines
            continue
        " Indent is strictly less at this point: check for def/class
        elseif line =~ pattern && line !~ '^\s*@'
            return lnum
        endif
        let indent = indent(lnum)
    endwhile
    return 0
endfunction "}}}


fun! s:BlockEnd(lnum, ...) "{{{
    let indent = a:0 ? a:1 : indent(a:lnum)
    let lnum = a:lnum
    while lnum
        let lnum = nextnonblank(lnum + 1)
        if getline(lnum) =~ '^\s*#' | continue
        elseif lnum && indent(lnum) <= indent
            return lnum - 1
        endif
    endwhile
    return line('$')
endfunction "}}}
" vim: fdm=marker:fdl=0
