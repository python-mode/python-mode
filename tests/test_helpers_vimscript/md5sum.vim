" Define md5sum hash function.
function! Md5()
python3 << EOF
import vim
from hashlib import md5
hasher = md5()
cb = vim.current.buffer
with open(cb.name, 'rb') as f:
    hasher.update(f.read())
cb.vars['calculated_md5'] = hasher.hexdigest()
# vim.command('let md5digest = ' + hasher.hexdigest())
EOF
" echom md5digest
endfunction
