" OPTION: g:pymode_lint -- bool. Load pylint plugin
call helpers#SafeVar("g:pymode_virtualenv", 1)

" DESC: Disable script loading
if !g:pymode_virtualenv || !g:pymode
    let g:pymode_virtualenv = 0
    finish
endif

fun! pymode_virtualenv#Activate() "{{{
python << EOF
ve_dir = os.environ['VIRTUAL_ENV']
ve_dir in sys.path or sys.path.insert(0, ve_dir)
activate_this = os.path.join(os.path.join(ve_dir, 'bin'), 'activate_this.py')
execfile(activate_this, dict(__file__=activate_this))
EOF
endfunction "}}}
