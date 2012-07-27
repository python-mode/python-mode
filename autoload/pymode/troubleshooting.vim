" DESC: Get debug information about pymode problem
fun! pymode#troubleshooting#Test() "{{{
    new
    setlocal buftype=nofile bufhidden=delete noswapfile nowrap
    call append('0', ['Pymode diagnostic',
                  \ '===================',
                  \ 'VIM:' . v:version . ' multi_byte:' . has('multi_byte') . ' pymode: ' . g:pymode_version,
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
    call append('$', 'pymode:' . g:pymode)
    call append('$', 'pymode_lint:' . g:pymode_lint)
    call append('$', 'pymode_rope:' . g:pymode_rope)
    call append('$', 'pymode_path:' . g:pymode_path)
    call append('$', 'pymode_doc:' . g:pymode_doc)
    call append('$', 'pymode_run:' . g:pymode_run)
    call append('$', 'pymode_virtualenv:' . g:pymode_virtualenv)
    call append('$', 'pymode_breakpoint:' . g:pymode_breakpoint)
    call append('$', 'pymode_path:' . g:pymode_path)
    call append('$', 'pymode_folding:' . g:pymode_folding)
    call append('$', 'pymode_syntax:' . g:pymode_syntax)
    call append('$', 'pymode_utils_whitespaces:' . g:pymode_utils_whitespaces)
    call append('$', 'pymode_options_indent:' . g:pymode_options_indent)
    call append('$', 'pymode_options_other:' . g:pymode_options_other)

    if len(g:pymode_virtualenv_enabled)
        call append('$', 'Enabled virtualenv:')
        call append('$', '-------------------')
        call append('$', g:pymode_virtualenv_enabled)
        call append('$', '')
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
