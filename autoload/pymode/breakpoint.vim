fun! pymode#breakpoint#init() "{{{

    " If breakpoints are either disabled or already defined do nothing.
    if ! g:pymode_breakpoint || g:pymode_breakpoint_cmd != ''
        return

    " Else go for a 'smart scan' of the defaults.
    else

        PymodePython << EOF

from pymode.libs.six import PY3

if PY3:
    from importlib.util import find_spec
    def module_exists(module_name):
        return find_spec(module_name)
else:
    from imp import find_module
    def module_exists(module_name):
        try:
            return find_module(module_name)
        except ImportError:
            return False

for module in ('wdb', 'pudb', 'ipdb', 'pdb'):
    if module_exists(module):
        vim.command('let g:pymode_breakpoint_cmd = "import %s; %s.set_trace()  # XXX BREAKPOINT"' % (module, module))
        break
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
