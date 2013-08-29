fun! pymode#path#Activate(plugin_root) "{{{

python << EOF
import sys, vim, os

curpath = vim.eval("getcwd()")
libpath = os.path.join(vim.eval("a:plugin_root"), 'pylibs')

sys.path = [libpath, curpath] + vim.eval("g:pymode_paths") + sys.path
EOF

endfunction "}}}
