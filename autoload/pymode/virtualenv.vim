fun! pymode#virtualenv#Activate() "{{{

    if !exists("$VIRTUAL_ENV")
        return
    endif

    for env in g:pymode_virtualenv_enabled
        if env == $VIRTUAL_ENV
            return 0
        endif
    endfor

    call add(g:pymode_virtualenv_enabled, $VIRTUAL_ENV)

Python << EOF
import sys, vim, os

ve_dir = vim.eval('$VIRTUAL_ENV')
ve_dir in sys.path or sys.path.insert(0, ve_dir)
activate_this = os.path.join(os.path.join(ve_dir, 'bin'), 'activate_this.py')

# Fix for windows
if not os.path.exists(activate_this):
    activate_this = os.path.join(os.path.join(ve_dir, 'Scripts'), 'activate_this.py')

f = open(activate_this)
try:
    source = f.read()
finally:
    f.close()

exec(compile(source, activate_this, 'exec'), dict(__file__=activate_this))
EOF

    call pymode#WideMessage("Activate virtualenv: ".$VIRTUAL_ENV)

endfunction "}}}
