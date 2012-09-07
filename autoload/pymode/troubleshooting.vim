" DESC: Get debug information about pymode problem
fun! pymode#troubleshooting#Test() "{{{
    new
    setlocal buftype=nofile bufhidden=delete noswapfile nowrap

    let os = "Unknown"
    if has('win16') || has('win32') || has('win64')
        let os = "Windows"
    else
        let os = substitute(system('uname'), "\n", "", "")
    endif

    call append('0', ['Pymode diagnostic',
                  \ '===================',
                  \ 'VIM:' . v:version . ', OS: ' . os .', multi_byte:' .  has('multi_byte') . ', pymode: ' . g:pymode_version,
                  \ ''])

    let python = 1
    let output = []

    if !exists('#filetypeplugin')
        call append('$', ['WARNING: ', 'Python-mode required :filetype plugin indent on', ''])
    endif

    if !has('python')
        call append('$', ['WARNING: ', 'Python-mode required vim compiled with +python.',
                        \ '"lint, rope, run, doc, virtualenv" features disabled.', ''])
        let python = 0
    endif

    call append('$', 'Pymode variables:')
    call append('$', '-------------------')
    call append('$', 'let pymode = ' . string(g:pymode))
    if g:pymode
        call append('$', 'let pymode_path = ' . string(g:pymode_path))
        call append('$', 'let pymode_paths = ' . string(g:pymode_paths))

        call append('$', 'let pymode_doc = ' . string(g:pymode_doc))
        if g:pymode_doc
            call append('$', 'let pymode_doc_key = ' . string(g:pymode_doc_key))
        endif

        call append('$', 'let pymode_run = ' . string(g:pymode_run))
        if g:pymode_run
            call append('$', 'let pymode_run_key = ' . string(g:pymode_run_key))
        endif

        call append('$', 'let pymode_lint = ' . string(g:pymode_lint))
        if g:pymode_lint
            call append('$', 'let pymode_lint_checker = ' . string(g:pymode_lint_checker))
            call append('$', 'let pymode_lint_ignore = ' . string(g:pymode_lint_ignore))
            call append('$', 'let pymode_lint_select = ' . string(g:pymode_lint_select))
            call append('$', 'let pymode_lint_onfly = ' . string(g:pymode_lint_onfly))
            call append('$', 'let pymode_lint_config = ' . string(g:pymode_lint_config))
            call append('$', 'let pymode_lint_write = ' . string(g:pymode_lint_write))
            call append('$', 'let pymode_lint_cwindow = ' . string(g:pymode_lint_cwindow))
            call append('$', 'let pymode_lint_message = ' . string(g:pymode_lint_message))
            call append('$', 'let pymode_lint_signs = ' . string(g:pymode_lint_signs))
            call append('$', 'let pymode_lint_jump = ' . string(g:pymode_lint_jump))
            call append('$', 'let pymode_lint_hold = ' . string(g:pymode_lint_hold))
            call append('$', 'let pymode_lint_minheight = ' .  string(g:pymode_lint_minheight))
            call append('$', 'let pymode_lint_maxheight = ' .  string(g:pymode_lint_maxheight)) 
        endif

        call append('$', 'let pymode_rope = ' . string(g:pymode_rope))
        call append('$', 'let pymode_folding = ' . string(g:pymode_folding))
        call append('$', 'let pymode_breakpoint = ' . string(g:pymode_breakpoint))
        call append('$', 'let pymode_syntax = ' . string(g:pymode_syntax))
        call append('$', 'let pymode_virtualenv = ' . string(g:pymode_virtualenv))
        if g:pymode_virtualenv
            call append('$', 'let pymode_virtualenv_enabled = ' .  string(g:pymode_virtualenv_enabled))
        endif
        call append('$', 'pymode_utils_whitespaces:' . string(g:pymode_utils_whitespaces))
        call append('$', 'pymode_options:' . string(g:pymode_options))
    endif

    if python
        call append('$', 'VIM python paths:')
        call append('$', '-----------------')
python << EOF
vim.command('let l:output = %s' % repr(sys.path))
EOF
        call append('$', output)
        call append('$', '')
    endif
    
endfunction "}}}
