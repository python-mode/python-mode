" Python Options
setlocal complete+=t
setlocal cinwords=if,elif,else,for,while,try,except,finally,def,class
setlocal cindent
setlocal foldlevelstart=99
setlocal foldlevel=99
setlocal foldmethod=indent
setlocal formatoptions-=t
setlocal nowrap
setlocal number
setlocal tabstop=4
setlocal textwidth=80
setlocal softtabstop=4

" Fix path for project
if g:pymode

    py curpath = vim.eval('getcwd()')
    py curpath in sys.path or sys.path.append(curpath)

endif

" Add virtualenv paths
if g:pymode_virtualenv && exists("$VIRTUAL_ENV")
    call pymode_virtualenv#Activate()
endif

" Python documentation
if g:pymode_doc

    " DESC: Set commands
    command! -buffer -nargs=+ Pydoc call pymode_doc#Show("<args>")

    " DESC: Set keys
    exe "nnoremap <silent> <buffer> " g:pymode_doc_key ":call pymode_doc#Show(expand('<cword>'))<CR>"

endif


" PyLint
if g:pymode_lint

    " DESC: Set autocommands
    if g:pymode_lint_write
        au BufWritePost <buffer> call pymode_lint#Lint()
    endif

    " DESC: Set commands
    command! -buffer PyLintToggle :let g:pymode_lint = g:pymode_lint ? 0 : 1
    command! -buffer PyLint :call pymode_lint#Lint()

endif

" Rope
if g:pymode_rope

    " DESC: Set keys
    noremap <silent> <buffer> <C-c>g :RopeGotoDefinition<CR>
    noremap <silent> <buffer> <C-c>d :RopeShowDoc<CR>
    noremap <silent> <buffer> <C-c>f :RopeFindOccurences<CR>
    noremap <silent> <buffer> <C-c>m :emenu Rope.<TAB>
    inoremap <silent> <buffer> <Nul> <C-R>=RopeCodeAssistInsertMode()<CR>
    inoremap <silent> <buffer> <C-space> <C-R>=RopeCodeAssistInsertMode()<CR>
    inoremap <silent> <buffer> <S-TAB> <C-R>=RopeLuckyAssistInsertMode()<CR>

endif

" Run code
if g:pymode_run

    " DESC: Set commands
    command! -buffer Pyrun call pymode_run#Run()

    " DESC: Set keys
    exe "nnoremap <silent> <buffer> " g:pymode_run_key ":Pyrun<CR>"

endif

" Set breakpoints
if g:pymode_breakpoint

    " DESC: Set keys
    exe "nnoremap <silent> <buffer> " g:pymode_breakpoint_key ":call pymode_breakpoint#Set(line('.'))<CR>"

endif

" OPTION: g:pymode_utils_whitespaces -- bool. Remove unused whitespaces on save
call helpers#SafeVar("g:pymode_utils_whitespaces", 1)

" Utils whitespaces
if g:pymode_utils_whitespaces
    au BufWritePre <buffer> :call setline(1,map(getline(1,"$"),'substitute(v:val,"\\s\\+$","","")'))
endif
