" Python-mode folding functions


let s:defpat = '^\s*\(@\|class\s.*:\|def\s\)'


fun! pymode#folding#text() " {{{
    let fs = v:foldstart
    while getline(fs) =~ '^\s*@' 
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
    let fillcharcount = windowwidth - len(line) - len(foldedlinecount)
    return line . '…' . repeat(" ",fillcharcount) . foldedlinecount . '…' . ' '
endfunction "}}}


fun! pymode#folding#indent(lnum) "{{{
    let indent = indent(pymode#BlockStart(a:lnum))
    return indent ? indent + &shiftwidth : 0
endfunction "}}}


fun! pymode#folding#expr(lnum) "{{{
    let line = getline(a:lnum)
    let indent = indent(a:lnum)

    if line == ''
        return getline(a:lnum+1) == '' ? '=' : '-1'
    endif

    if line =~ s:defpat && getline(prevnonblank(a:lnum-1)) !~ '^\s*@'
        let n = a:lnum
        while getline(n) =~ '^\s*@'
            let n = nextnonblank(n + 1)
        endwhile
        if getline(n) =~ s:defpat
            return ">".(indent/&shiftwidth+1)
        endif
    endif

    let p = prevnonblank(a:lnum-1)
    while p>0 && getline(p) =~ '^\s*#'
        let p = prevnonblank(p-1)
    endwhile
    let pind = indent(p)
    if getline(p) =~ s:defpat && getline(prevnonblank(a:lnum - 1)) !~ '^\s*@'
        let pind = pind + &shiftwidth
    elseif p==0
        let pind = 0
    endif

    if (indent>0 && indent==pind) || indent>pind
        return '='
    elseif indent==0
        if pind==0 && line =~ '^#'
            return 0
        elseif line !~'^#'
            if 0<pind && line!~'^else\s*:\|^except.*:\|^elif.*:\|^finally\s*:'
                return '>1'
            elseif 0==pind && getline(prevnonblank(a:lnum-1)) =~ '^\s*#'
                return '>1'
            else
                return '='
            endif
        endif
        let n = nextnonblank(a:lnum+1)
        while n>0 && getline(n) =~'^\s*#'
            let n = nextnonblank(n+1)
        endwhile
        if indent(n)==0
            return 0
        else
            return -1
        end
    endif
    let blockindent = indent(pymode#BlockStart(a:lnum)) + &shiftwidth
    if blockindent==0
        return 1
    endif
    let n = nextnonblank(a:lnum+1)
    while n>0 && getline(n) =~'^\s*#'
        let n = nextnonblank(n+1)
    endwhile
    let nind = indent(n)
    if line =~ '^\s*#' && indent>=nind
        return -1
    elseif line =~ '^\s*#'
        return nind / &shiftwidth
    else
        return blockindent / &shiftwidth
    endif
endfunction "}}}


" vim: fdm=marker:fdl=0
