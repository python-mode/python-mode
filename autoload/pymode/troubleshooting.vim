" DESC: Get debug information about pymode problem
fun! pymode#troubleshooting#test() "{{{
    new
    setlocal buftype=nofile bufhidden=delete noswapfile nowrap

    let os = "Unknown"
    if has('win16') || has('win32') || has('win64')
        let os = "Windows"
    else
        let os = substitute(system('uname'), "\n", "", "")
    endif

    if !pymode#default('g:pymode_init', 1)
        call pymode#init(expand('<sfile>:p:h'), g:pymode_paths)
        call pymode#virtualenv#init()
        call pymode#breakpoint#init()
    endif

    call append('0', ['Pymode diagnostic',
                  \ '===================',
                  \ 'VIM:' . v:version . ', OS: ' . os .', multi_byte:' .  has('multi_byte') . ', pymode: ' . g:pymode_version . ', pymode-python: ' . g:pymode_python, 
                  \ ''])

    if !exists('#filetypeplugin')
        call append('$', ['WARNING: ', 'Python-mode required :filetype plugin indent on', ''])
    endif

    call append('$', ['+python: ' . has('python')])
    call append('$', ['+python3: ' . has('python3'), ''])

    if g:pymode_python == 'disable'

        if !has('python') && !has('python3')

            call append('$', ['WARNING: Python-mode required vim compiled with +python or +python3.',
                            \ '"lint, rope, run, doc, virtualenv" features disabled.', ''])

        else

            call append('$', ['WARNING: Python is disabled by `pymode_python` option.',
                            \ '"lint, rope, run, doc, virtualenv" features disabled.', ''])

        endif

    else

        call append('$', 'VIM python paths:')
        call append('$', '-----------------')
    PymodePython << EOF
import vim
vim.command('let l:output = %s' % repr(sys.path))
EOF
        call append('$', output)
        call append('$', '')

    endif

    call append('$', 'Pymode variables:')
    call append('$', '-------------------')
    call append('$', 'let pymode = ' . string(g:pymode))
    call append('$', 'let pymode_breakpoint = ' . string(g:pymode_breakpoint))
    call append('$', 'let pymode_breakpoint_bind = ' . string(g:pymode_breakpoint_bind))
    call append('$', 'let pymode_doc = ' . string(g:pymode_doc))
    call append('$', 'let pymode_doc_bind = ' . string(g:pymode_doc_bind))
    call append('$', 'let pymode_folding = ' . string(g:pymode_folding))
    call append('$', 'let pymode_indent = ' . string(g:pymode_indent))
    call append('$', 'let pymode_lint = ' . string(g:pymode_lint))
    call append('$', 'let pymode_lint_checkers = ' . string(g:pymode_lint_checkers))
    call append('$', 'let pymode_lint_cwindow = ' . string(g:pymode_lint_cwindow))
    call append('$', 'let pymode_lint_ignore = ' . string(g:pymode_lint_ignore))
    call append('$', 'let pymode_lint_message = ' . string(g:pymode_lint_message))
    call append('$', 'let pymode_lint_on_fly = ' . string(g:pymode_lint_on_fly))
    call append('$', 'let pymode_lint_on_write = ' . string(g:pymode_lint_on_write))
    call append('$', 'let pymode_lint_select = ' . string(g:pymode_lint_select))
    call append('$', 'let pymode_lint_signs = ' . string(g:pymode_lint_signs))
    call append('$', 'let pymode_motion = ' . string(g:pymode_motion))
    call append('$', 'let pymode_options = ' . string(g:pymode_options))
    call append('$', 'let pymode_paths = ' . string(g:pymode_paths))
    call append('$', 'let pymode_quickfix_maxheight = ' . string(g:pymode_quickfix_maxheight))
    call append('$', 'let pymode_quickfix_minheight = ' . string(g:pymode_quickfix_minheight))
    call append('$', 'let pymode_rope = ' . string(g:pymode_rope))
    call append('$', 'let pymode_run = ' . string(g:pymode_run))
    call append('$', 'let pymode_run_bind = ' . string(g:pymode_run_bind))
    call append('$', 'let pymode_trim_whitespaces = ' . string(g:pymode_trim_whitespaces))
    call append('$', 'let pymode_virtualenv = ' . string(g:pymode_virtualenv))
    call append('$', 'let pymode_virtualenv_enabled = ' . string(g:pymode_virtualenv_enabled))
    call append('$', 'let pymode_virtualenv_path = ' . string(g:pymode_virtualenv_path))
    
endfunction "}}}
