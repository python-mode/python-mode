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

fun! pymode#motion#select(first_pattern, second_pattern, inner) "{{{
    let cnt = v:count1 - 1
    let orig = getpos('.')[1:2]
    let posns = s:BlockStart(orig[0], a:first_pattern, a:second_pattern)
    if getline(posns[0]) !~ a:first_pattern && getline(posns[0]) !~ a:second_pattern
        return 0
    endif
    let snum = posns[0]
    let enum = s:BlockEnd(posns[1], indent(posns[1]))
    while cnt
        let lnum = search(a:second_pattern, 'nW')
        if lnum
            let enum = s:BlockEnd(lnum, indent(lnum))
            call cursor(enum, 1)
        endif
        let cnt = cnt - 1
    endwhile
    if pymode#motion#pos_le([snum, 0], orig) && pymode#motion#pos_le(orig, [enum+1, 0])
        if a:inner
            let snum = posns[1] + 1
        endif

        call cursor(snum, 1)
        normal! v
        call cursor(enum, len(getline(enum)))
    endif
endfunction "}}}

fun! pymode#motion#select_c(pattern, inner) "{{{
    call pymode#motion#select(a:pattern, a:pattern, a:inner)
endfunction "}}}

fun! s:BlockStart(lnum, first_pattern, second_pattern) "{{{
    let lnum = a:lnum + 1
    let indent = 100
    while lnum
        let lnum = prevnonblank(lnum - 1)
        let test = indent(lnum)
        let line = getline(lnum)
        " Skip comments, deeper or equal lines
        if line =~ '^\s*#' || test >= indent
            continue
        endif
        let indent = indent(lnum)

        " Indent is strictly less at this point: check for def/class/@
        if line =~ a:first_pattern || line =~ a:second_pattern
            while getline(lnum-1) =~ a:first_pattern
                let lnum = lnum - 1
	    endwhile
	    let first_pos = lnum
	    while getline(lnum) !~ a:second_pattern
                let lnum = lnum + 1
            endwhile
	    let second_pos = lnum
            return [first_pos, second_pos]
        endif
    endwhile
    return [0, 0]
endfunction "}}}


fun! s:BlockEnd(lnum, ...) "{{{
    let indent = a:0 ? a:1 : indent(a:lnum)
    let lnum = a:lnum
    while lnum
        let lnum = nextnonblank(lnum + 1)
        if getline(lnum) =~ '^\s*#' | continue
        elseif lnum && indent(lnum) <= indent
            return prevnonblank(lnum - 1)
        endif
    endwhile
    return line('$')
endfunction "}}}
" vim: fdm=marker:fdl=0
