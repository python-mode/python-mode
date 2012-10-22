if pymode#Default('b:pymode', 1)
    finish
endif


" Parse pymode modeline
call pymode#Modeline()


" Syntax highlight
if pymode#Option('syntax')
    let python_highlight_all=1
endif


" Options {{{

" Python other options
if pymode#Option('options')
    setlocal complete+=t
    setlocal formatoptions-=t
    if v:version > 702 && !&relativenumber
        setlocal number
    endif
    setlocal nowrap
    setlocal textwidth=79
endif

" }}}


" Documentation {{{

if pymode#Option('doc')

    " DESC: Set commands
    command! -buffer -nargs=1 Pydoc call pymode#doc#Show("<args>")

    " DESC: Set keys
    exe "nnoremap <silent> <buffer> " g:pymode_doc_key ":call pymode#doc#Show(expand('<cword>'))<CR>"
    exe "vnoremap <silent> <buffer> " g:pymode_doc_key ":<C-U>call pymode#doc#Show(@*)<CR>"

endif

" }}}


" Lint {{{

if pymode#Option('lint')

    " DESC: Set commands
    command! -buffer -nargs=0 PyLintToggle :call pymode#lint#Toggle()
    command! -buffer -nargs=0 PyLintWindowToggle :call pymode#lint#ToggleWindow()
    command! -buffer -nargs=0 PyLintCheckerToggle :call pymode#lint#ToggleChecker()
    command! -buffer -nargs=0 PyLint :call pymode#lint#Check()
    command! -buffer -nargs=0 PyLintAuto :call pymode#lint#Auto()

    " DESC: Set autocommands
    if pymode#Option('lint_write')
        au BufWritePost <buffer> PyLint
    endif

    if pymode#Option('lint_onfly')
        au InsertLeave <buffer> PyLint
    endif

    if pymode#Option('lint_message')
        au CursorHold <buffer> call pymode#lint#show_errormessage()
        au CursorMoved <buffer> call pymode#lint#show_errormessage()
    endif

    " DESC: Run queue
    let &l:updatetime = g:pymode_updatetime
    au CursorHold <buffer> call pymode#queue#Poll()
    au BufLeave <buffer> py queue.stop_queue()

endif

" }}}


" Rope {{{

if pymode#Option('rope')

    " DESC: Set keys
    exe "noremap <silent> <buffer> " . g:pymode_rope_short_prefix . "g :RopeGotoDefinition<CR>"
    exe "noremap <silent> <buffer> " . g:pymode_rope_short_prefix . "d :RopeShowDoc<CR>"
    exe "noremap <silent> <buffer> " . g:pymode_rope_short_prefix . "f :RopeFindOccurrences<CR>"
    exe "noremap <silent> <buffer> " . g:pymode_rope_short_prefix . "m :emenu Rope . <TAB>"
    inoremap <silent> <buffer> <S-TAB> <C-R>=RopeLuckyAssistInsertMode()<CR>

    if g:pymode_rope_map_space
        let s:prascm = g:pymode_rope_always_show_complete_menu ? "<C-P>" : ""
        exe "inoremap <silent> <buffer> <Nul> <C-R>=RopeCodeAssistInsertMode()<CR>" . s:prascm
        exe "inoremap <silent> <buffer> <c-space> <C-R>=RopeCodeAssistInsertMode()<CR>" . s:prascm
    endif

endif

" }}}


" Execution {{{

if pymode#Option('run')

    " DESC: Set commands
    command! -buffer -nargs=0 -range=% Pyrun call pymode#run#Run(<f-line1>, <f-line2>)

    " DESC: Set keys
    exe "nnoremap <silent> <buffer> " g:pymode_run_key ":Pyrun<CR>"
    exe "vnoremap <silent> <buffer> " g:pymode_run_key ":Pyrun<CR>"

endif

" }}}


" Breakpoints {{{

if pymode#Option('breakpoint')

    " DESC: Set keys
    exe "nnoremap <silent> <buffer> " g:pymode_breakpoint_key ":call pymode#breakpoint#Set(line('.'))<CR>"

endif

" }}}


" Utils {{{

if pymode#Option('utils_whitespaces')
    au BufWritePre <buffer> call pymode#TrimWhiteSpace()
endif

" }}}


" Folding {{{

if pymode#Option('folding')

    setlocal foldmethod=expr
    setlocal foldexpr=pymode#folding#expr(v:lnum)
    setlocal foldtext=pymode#folding#text()

endif

" }}}

" vim: fdm=marker:fdl=0
