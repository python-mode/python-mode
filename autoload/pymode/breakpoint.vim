fun! pymode#breakpoint#init() "{{{

    if !g:pymode_breakpoint
        return
    endif

    if g:pymode_breakpoint_cmd == ''
        let g:pymode_breakpoint_cmd = 'import pdb; pdb.set_trace()  # XXX BREAKPOINT'

        if g:pymode_python == 'disable'
            return
        endif

    endif

        PymodePython << EOF

from imp import find_module

for module in ('pudb', 'ipdb'):
    try:
        find_module(module)
        vim.command('let g:pymode_breakpoint_cmd = "import %s; %s.set_trace()  # XXX BREAKPOINT"' % (module, module))
        break
    except ImportError:
        continue

EOF

endfunction "}}}

fun! pymode#breakpoint#operate(lnum) "{{{
    let line = getline(a:lnum)
    if strridx(line, g:pymode_breakpoint_cmd) != -1
        normal dd
    else
        let plnum = prevnonblank(a:lnum)
        call append(line('.')-1, repeat(' ', indent(plnum)).g:pymode_breakpoint_cmd)
        normal k
    endif

    " Save file without any events
    call pymode#save()

endfunction "}}}
