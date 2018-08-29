fun! pymode#breakpoint#init() "{{{

    " If breakpoints are either disabled or already defined do nothing.
    if ! g:pymode_breakpoint || g:pymode_breakpoint_cmd != ''
        return

    " Else go for a 'smart scan' of the defaults.
    else

        PymodePython << EOF

def find_spec(name):
    try:
        from importlib.util import find_spec
        if find_spec(name) is not None:
            return name
    except ImportError:
        try:
            from imp import find_module
            find_module(name)
            return name
        except ImportError:
            return None

for module in ('wdb', 'pudb', 'ipdb', 'pdb'):
    try:
        mod_ = find_spec(module)
        if mod_ is not None:
            vim.command('let g:pymode_breakpoint_cmd = "import %s; %s.set_trace()  # XXX BREAKPOINT"' % (module, module))
        break
    except ImportError:
        continue

EOF
    endif

endfunction "}}}

fun! pymode#breakpoint#operate(lnum) "{{{
    if g:pymode_breakpoint_cmd == ''
        echoerr("g:pymode_breakpoint_cmd is empty")
        return -1
    endif
    let line = getline(a:lnum)
    if strridx(line, g:pymode_breakpoint_cmd) != -1
        normal dd
    else
        let plnum = prevnonblank(a:lnum)
        if &expandtab
            let indents = repeat(' ', indent(plnum))
        else
            let indents = repeat("\t", plnum / &shiftwidth)
        endif

        call append(line('.')-1, indents.g:pymode_breakpoint_cmd)
        normal k
    endif

    " Save file without any events
    call pymode#save()

endfunction "}}}
