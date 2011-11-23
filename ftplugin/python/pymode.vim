if pymode#Default('b:pymode', 1)
    finish
endif

" Syntax highlight
if !pymode#Default('g:pymode_syntax', 1) || g:pymode_syntax
    let python_highlight_all=1
endif

" Python indent options
if !pymode#Default('g:pymode_options_indent', 1) || g:pymode_options_indent
    setlocal cinwords=if,elif,else,for,while,try,except,finally,def,class
    setlocal cindent
    setlocal tabstop=4
    setlocal softtabstop=4
    setlocal shiftwidth=4
    setlocal shiftround
    setlocal smartindent
    setlocal smarttab
    setlocal expandtab
    setlocal autoindent
endif

" Python fold options
if !pymode#Default('g:pymode_options_fold', 1) || g:pymode_options_fold
    setlocal foldlevelstart=99
    setlocal foldlevel=99
    setlocal foldmethod=indent
endif
      
" Python other options
if !pymode#Default('g:pymode_options_other', 1) || g:pymode_options_other
    setlocal complete+=t
    setlocal formatoptions-=t
    setlocal number
    setlocal nowrap
    setlocal textwidth=80
endif

" Fix path for project
if g:pymode
    py curpath = vim.eval('getcwd()')
    py curpath in sys.path or sys.path.append(curpath)
endif

" Add virtualenv paths
if g:pymode_virtualenv && exists("$VIRTUAL_ENV")
    call pymode#virtualenv#Activate()
endif

" Python documentation
if g:pymode_doc

    " DESC: Set commands
    command! -buffer -nargs=1 Pydoc call pymode#doc#Show("<args>")

    " DESC: Set keys
    exe "nnoremap <silent> <buffer> " g:pymode_doc_key ":call pymode#doc#Show(expand('<cword>'))<CR>"

endif


" PyLint
if g:pymode_lint

    " DESC: Set commands
    command! -buffer -nargs=0 PyLintToggle :call pymode#lint#Toggle()
    command! -buffer -nargs=0 PyLintCheckerToggle :call pymode#lint#ToggleChecker()
    command! -buffer -nargs=0 PyLint :call pymode#lint#Check()

    " DESC: Set autocommands
    if g:pymode_lint_write
        au BufWritePost <buffer> PyLint
    endif

endif

" Rope
if g:pymode_rope

    " DESC: Set keys
    noremap <silent> <buffer> <C-c>g :RopeGotoDefinition<CR>
    noremap <silent> <buffer> <C-c>d :RopeShowDoc<CR>
    noremap <silent> <buffer> <C-c>f :RopeFindOccurrences<CR>
    noremap <silent> <buffer> <C-c>m :emenu Rope.<TAB>
    inoremap <silent> <buffer> <S-TAB> <C-R>=RopeLuckyAssistInsertMode()<CR>

    let s:prascm = g:pymode_rope_always_show_complete_menu ? "<C-P>" : ""    
    exe "inoremap <silent> <buffer> <Nul> <C-R>=RopeCodeAssistInsertMode()<CR>" . s:prascm
    exe "inoremap <silent> <buffer> <C-space> <C-R>=RopeCodeAssistInsertMode()<CR>" . s:prascm

endif

" Run code
if g:pymode_run

    " DESC: Set commands
    command! -buffer -nargs=0 Pyrun call pymode#run#Run()

    " DESC: Set keys
    exe "nnoremap <silent> <buffer> " g:pymode_run_key ":Pyrun<CR>"

endif

" Set breakpoints
if g:pymode_breakpoint

    " DESC: Set keys
    exe "nnoremap <silent> <buffer> " g:pymode_breakpoint_key ":call pymode#breakpoint#Set(line('.'))<CR>"

endif

" OPTION: g:pymode_utils_whitespaces -- bool. Remove unused whitespaces on save
call pymode#Default("g:pymode_utils_whitespaces", 1)

" Utils whitespaces
if g:pymode_utils_whitespaces
    au BufWritePre <buffer> :call setline(1,map(getline(1,"$"),'substitute(v:val,"\\s\\+$","","")'))
endif
