fun! pymode#path#Activate(plugin_root) "{{{

Python << EOF
import sys, vim, os

pymode_lib = 'pylibs'

# if sys.version >= (3, 0, 0):
#    pymode_lib = 'pylibs3'

curpath = vim.eval("getcwd()")
libpath = os.path.join(vim.eval("a:plugin_root"), pymode_lib)

sys.path = [libpath, curpath] + vim.eval("g:pymode_paths") + sys.path
EOF

endfunction "}}}
