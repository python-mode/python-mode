" Python-mode folding functions
" Notice that folding is based on single line so complex regular expressions
" that take previous line into consideration are not fit for the job.

" Regex definitions for correct folding
let s:def_regex = g:pymode_folding_regex
let s:blank_regex = '^\s*$'
" Spyder, a very popular IDE for python has a template which includes
" '@author:' ; thus the regex below.
let s:decorator_regex = '^\s*@\(author:\)\@!'
let s:docstring_line_regex = '^\s*[uUrR]\=\("""\|''''''\).\+\1\s*$'
let s:docstring_begin_regex = '^\s*[uUrR]\=\%("""\|''''''\).*\S'
let s:docstring_end_regex = '\%("""\|''''''\)\s*$'
" This one is needed for the while loop to count for opening and closing
" docstrings.
let s:docstring_general_regex = '\%("""\|''''''\)'
let s:symbol = matchstr(&fillchars, 'fold:\zs.')  " handles multibyte characters
if s:symbol == ''
    let s:symbol = ' '
endif
" ''''''''


fun! pymode#folding#text() " {{{
    let fs = v:foldstart
    while getline(fs) !~ s:def_regex && getline(fs) !~ s:docstring_begin_regex
        let fs = nextnonblank(fs + 1)
    endwhile
    if getline(fs) =~ s:docstring_end_regex && getline(fs) =~ s:docstring_begin_regex
        let fs = nextnonblank(fs + 1)
    endif
    let line = getline(fs)

    let has_numbers = &number || &relativenumber
    let nucolwidth = &fdc + has_numbers * &numberwidth
    let windowwidth = winwidth(0) - nucolwidth - 6
    let foldedlinecount = v:foldend - v:foldstart

    " expand tabs into spaces
    let onetab = strpart('          ', 0, &tabstop)
    let line = substitute(line, '\t', onetab, 'g')

    let line = strpart(line, 0, windowwidth - 2 -len(foldedlinecount))
    let line = substitute(line, '[uUrR]\=\%("""\|''''''\)', '', '')
    let fillcharcount = windowwidth - len(line) - len(foldedlinecount) + 1
    return line . ' ' . repeat(s:symbol, fillcharcount) . ' ' . foldedlinecount
endfunction "}}}

fun! pymode#folding#expr(lnum) "{{{

    let line = getline(a:lnum)
    let indent = indent(a:lnum)
    let prev_line = getline(a:lnum - 1)
    let next_line = getline(a:lnum + 1)

    " Decorators {{{
    if line =~ s:decorator_regex
        return ">".(indent / &shiftwidth + 1)
    endif "}}}

    " Definition {{{
    if line =~ s:def_regex
        " If indent of this line is greater or equal than line below
        " and previous non blank line does not end with : (that is, is not a
        " definition)
        " Keep the same indentation
        if indent(a:lnum) >= indent(a:lnum+1) && getline(prevnonblank(a:lnum)) !~ ':\s*$'
            return '='
        endif
        " Check if last decorator is before the last def
        let decorated = 0
        let lnum = a:lnum - 1
        while lnum > 0
            if getline(lnum) =~ s:def_regex
                break
            elseif getline(lnum) =~ s:decorator_regex
                let decorated = 1
                break
            endif
            let lnum -= 1
        endwhile
        if decorated
            return '='
        else
            " The line below may improve folding.
            return ">".(indent / &shiftwidth + 1)
            " This was the previous rule. It grouped classes definitions
            " together (undesired).
            " return indent / &shiftwidth + 1
        endif
    endif "}}}

    " Docstrings {{{

    " TODO: A while loop now counts the number of open and closed folding in
    " order to determine if it is a closing or opening folding.
    " It is working but looks like it is an overkill.

    " Notice that an effect of this is that other docstring matches will not
    " be one liners.
    if line =~ s:docstring_line_regex
        return "="
    endif

    if line =~ s:docstring_begin_regex
        if s:Is_opening_folding(a:lnum)
            return ">".(indent / &shiftwidth + 1)
        endif
    endif
    if line =~ s:docstring_end_regex
        if !s:Is_opening_folding(a:lnum)
            return "<".(indent / &shiftwidth + 1)
        endif
    endif "}}}

    " Blocks. {{{
    let save_cursor = getcurpos()
    if line !~ s:blank_regex
        let line_block_start = s:BlockStart(a:lnum)
        let prev_line_block_start = s:BlockStart(a:lnum - 1)
        call setpos('.', save_cursor)
        if line_block_start == prev_line_block_start || a:lnum  - line_block_start == 1
            return '='
        elseif indent < indent(prevnonblank(a:lnum - 1))
            return indent(line_block_start) / &shiftwidth + 1
        else
        endif
    endif
    " endif " }}}

    " Blank Line {{{
    if line =~ s:blank_regex
        if prev_line =~ s:blank_regex
            if indent(a:lnum + 1) == 0 && next_line !~ s:blank_regex && next_line !~ s:docstring_general_regex
                if s:Is_opening_folding(a:lnum)
                    return "="
                else
                    return 0
                endif
            endif
            return -1
        else
            return '='
        endif
    endif " }}}

    return '='

endfunction "}}}

fun! s:BlockStart(line_number) "{{{
    " Returns the definition statement which encloses the current line.

    " Note: Make sure to reset cursor position after using this function.
    call cursor(a:line_number, 0)

    " In case the end of the block is indented to a higher level than the def
    " statement plus one shiftwidth, we need to find the indent level at the
    " bottom of that if/for/try/while/etc. block.
    let previous_definition = searchpos(s:def_regex, 'bcnW')
    if previous_definition != [0, 0]
        while previous_definition != [0, 0] && indent(previous_definition[0]) >= indent(a:line_number)
            let previous_definition = searchpos(s:def_regex, 'bncW')
            call cursor(previous_definition[0] - 1, 0)
        endwhile
    endif
    let last_def = previous_definition[0]
    if last_def
        call cursor(last_def, 0)
        let last_def_indent = indent(last_def)
        call cursor(last_def, 0)
        let next_stmt_at_def_indent = searchpos('\v^\s{'.last_def_indent.'}[^[:space:]#]', 'nW')[0]
    else
        let next_stmt_at_def_indent = -1
    endif

    " Now find the class/def one shiftwidth lower than the start of the
    " aforementioned indent block.
    if next_stmt_at_def_indent && next_stmt_at_def_indent < a:line_number
        let max_indent = max([indent(next_stmt_at_def_indent) - &shiftwidth, 0])
    else
        let max_indent = max([indent(prevnonblank(a:line_number)) - &shiftwidth, 0])
    endif

    " " Debug:

    return searchpos('\v^\s{,'.max_indent.'}(def |class )\w', 'bcnW')[0]

endfunction "}}}
function! Blockstart(x)
    let save_cursor = getcurpos()
    return s:BlockStart(a:x)
    call setpos('.', save_cursor)
endfunction

fun! s:BlockEnd(lnum) "{{{
    " Note: Make sure to reset cursor position after using this function.
    call cursor(a:lnum, 0)
    return searchpos('\v^\s{,'.indent('.').'}\S', 'nW')[0] - 1
endfunction "}}}
function! Blockend(lnum)
    let save_cursor = getcurpos()
    return s:BlockEnd(a:lnum)
    call setpos('.', save_cursor)
endfunction

function! s:Is_opening_folding(lnum) "{{{
    " Helper function to see if docstring is opening or closing

    " Cache the result so the loop runs only once per change
    if get(b:, 'fold_changenr', -1) == changenr()
        return b:fold_cache[a:lnum]  "If odd then it is an opening
    else
        let b:fold_changenr = changenr()
        let b:fold_cache = []
    endif

    let number_of_folding = 0  " To be analized if odd/even to inform if it is opening or closing.
    let has_open_docstring = 0  " To inform is already has an open docstring.
    let extra_docstrings = 0  " To help skipping ''' and """ which are not docstrings

    " The idea of this part of the function is to identify real docstrings and
    " not just triple quotes (that could be a regular string).
    "
    " Iterater over all lines from the start until current line (inclusive)
    for i in range(1, line('$'))
        call add(b:fold_cache, number_of_folding % 2)

        let i_line = getline(i)

        if i_line =~ s:docstring_line_regex
            continue
        endif

        if i_line =~ s:docstring_begin_regex && ! has_open_docstring
            " This causes the loop to continue if there is a triple quote which
            " is not a docstring.
            if extra_docstrings > 0
                let extra_docstrings = extra_docstrings - 1
                continue
            else
                let has_open_docstring = 1
                let number_of_folding = number_of_folding + 1
            endif
        " If it is an end doc and has an open docstring.
        elseif i_line =~ s:docstring_end_regex && has_open_docstring
            let has_open_docstring = 0
            let number_of_folding = number_of_folding + 1

        elseif i_line =~ s:docstring_general_regex
            let extra_docstrings = extra_docstrings + 1
        endif
    endfor

    call add(b:fold_cache, number_of_folding % 2)

    return b:fold_cache[a:lnum]
endfunction "}}}

" vim: fdm=marker:fdl=0
