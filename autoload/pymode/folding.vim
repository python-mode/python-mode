" Python-mode folding functions


let s:blank_regex = '^\s*$'
let s:def_regex = '^\s*\%(class\|def\) \w\+'
let s:decorator_regex = '^\s*@'
let s:doc_begin_regex = '^\s*\%("""\|''''''\)'
let s:doc_end_regex = '\%("""\|''''''\)\s*$'
let s:doc_line_regex = '^\s*\("""\|''''''\).\+\1\s*$'


fun! pymode#folding#text() " {{{
    let fs = v:foldstart
    while getline(fs) =~ '\%(^\s*@\)\|\%(^\s*\%("""\|''''''\)\s*$\)'
        let fs = nextnonblank(fs + 1)
    endwhile
    let line = getline(fs)

    let nucolwidth = &fdc + &number * &numberwidth
    let windowwidth = winwidth(0) - nucolwidth - 3
    let foldedlinecount = v:foldend - v:foldstart

    " expand tabs into spaces
    let onetab = strpart('          ', 0, &tabstop)
    let line = substitute(line, '\t', onetab, 'g')

    let line = strpart(line, 0, windowwidth - 2 -len(foldedlinecount))
    let line = substitute(line, '\%("""\|''''''\)', '', '')
    let fillcharcount = windowwidth - len(line) - len(foldedlinecount)
    return line . '…' . repeat(" ",fillcharcount) . foldedlinecount . '…' . ' '
endfunction "}}}


fun! pymode#folding#expr(lnum) "{{{

    let line = getline(a:lnum)
    let indent = indent(a:lnum)
	let prev_line = getline(a:lnum - 1)

    if line =~ s:def_regex || line =~ s:decorator_regex
		if prev_line =~ s:decorator_regex
			return '='
		else
			return ">".(indent / &shiftwidth + 1)
		endif
    endif

    if line =~ s:doc_begin_regex
				\ && line !~ s:doc_line_regex
				\ && prev_line =~ s:def_regex
		return ">".(indent / &shiftwidth + 1)
    endif

    if line =~ s:doc_end_regex
				\ && line !~ s:doc_line_regex
		return "<".(indent / &shiftwidth + 1)
    endif

    if line =~ s:blank_regex
        if prev_line =~ s:blank_regex
            return -1
        else
            return '='
        endif
    endif

    if indent == 0
        return 0
    endif

    return '='

endfunction "}}}


" vim: fdm=marker:fdl=0
