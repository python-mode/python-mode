" Python-mode folding functions


let s:def_regex = g:pymode_folding_regex
let s:blank_regex = '^\s*$'
let s:decorator_regex = '^\s*@'
let s:doc_begin_regex = '^\s*\%("""\|''''''\)'
let s:doc_end_regex = '\%("""\|''''''\)\s*$'
let s:doc_line_regex = '^\s*\("""\|''''''\).\+\1\s*$'
let s:symbol = matchstr(&fillchars, 'fold:\zs.')  " handles multibyte characters
if s:symbol == ''
    let s:symbol = ' '
endif


fun! pymode#folding#text() " {{{
    let fs = v:foldstart
    while getline(fs) =~ '\%(^\s*@\)\|\%(^\s*\%("""\|''''''\)\s*$\)'
        let fs = nextnonblank(fs + 1)
    endwhile
    let line = getline(fs)

    let nucolwidth = &fdc + &number * &numberwidth
    let windowwidth = winwidth(0) - nucolwidth - 6
    let foldedlinecount = v:foldend - v:foldstart

    " expand tabs into spaces
    let onetab = strpart('          ', 0, &tabstop)
    let line = substitute(line, '\t', onetab, 'g')

    let line = strpart(line, 0, windowwidth - 2 -len(foldedlinecount))
    let line = substitute(line, '\%("""\|''''''\)', '', '')
    let fillcharcount = windowwidth - len(line) - len(foldedlinecount) + 1
    return line . ' ' . repeat(s:symbol, fillcharcount) . ' ' . foldedlinecount
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

    if line =~ s:doc_begin_regex && line !~ s:doc_line_regex && prev_line =~ s:def_regex
        return ">".(indent / &shiftwidth + 1)
    endif

    if line =~ s:doc_end_regex && line !~ s:doc_line_regex
        return "<".(indent / &shiftwidth + 1)
    endif

    " Handle nested defs
    if indent(prevnonblank(a:lnum))
        let curpos = getcurpos()
        try
            let last_block = s:BlockStart(a:lnum)
            let last_block_indent = indent(last_block)

            " Check if last class/def is not indented and therefore can't be
            " nested.
            if last_block_indent
                " Note: This relies on the cursor position being set by s:BlockStart
                let next_def = searchpos(s:def_regex, 'nW')[0]
                let next_def_indent = next_def ? indent(next_def) : -1
                let last_block_end = s:BlockEnd(last_block)

                " If the next def has greater indent than the previous def, it
                " is nested one level deeper and will have its own fold. If
                " the class/def containing the current line is on the first
                " line it can't be nested, and if this block ends on the last
                " line, it contains no trailing code that should not be
                " folded. Finally, if the next non-blank line after the end of
                " the previous def is less indented than the previous def, it
                " is not part of the same fold as that def. Otherwise, we know
                " the current line is at the end of a nested def.
                if next_def_indent <= last_block_indent && last_block > 1 && last_block_end < line('$')
                    \ && indent(nextnonblank(last_block_end)) >= last_block_indent

                    " Include up to one blank line in the fold
                    if getline(last_block_end) =~ s:blank_regex
                        let fold_end = min([prevnonblank(last_block_end - 1), last_block_end]) + 1
                    else
                        let fold_end = last_block_end
                    endif
                    if a:lnum == fold_end
                        return 's1'
                    else
                        return '='
                    endif
                endif
            endif
        finally
            call setpos('.', curpos)
        endtry
    endif

    if line =~ s:blank_regex
        if prev_line =~ s:blank_regex
            if indent(a:lnum + 1) == 0 && getline(a:lnum + 1) !~ s:blank_regex
                return 0
            endif
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

fun! s:BlockStart(lnum) "{{{
    " Note: Make sure to reset cursor position after using this function.
    call cursor(a:lnum, 0)
    let max_indent = max([indent(prevnonblank(a:lnum)) - &shiftwidth, 0])
    return searchpos('\v^\s{,'.max_indent.'}(def |class )\w', 'bcnW')[0]
endfunction "}}}

fun! s:BlockEnd(lnum) "{{{
    " Note: Make sure to reset cursor position after using this function.
    call cursor(a:lnum, 0)
    return searchpos('\v^\s{,'.indent('.').'}\S', 'nW')[0] - 1
endfunction "}}}

" vim: fdm=marker:fdl=0
