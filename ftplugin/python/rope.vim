if helpers#SafeVar("g:python_rope", 1)
    finish
endif

python << EOF
import ropevim
EOF
let g:ropevim_loaded = 1

" RopeVim settings
let g:ropevim_codeassist_maxfixes=10
let g:ropevim_guess_project=1
let g:ropevim_vim_completion=1
let g:ropevim_enable_autoimport=1
let g:ropevim_autoimport_modules = ["os", "shutil"]

" Keys
imap <silent> <buffer> <Nul> <M-/>
imap <silent> <buffer> <C-Space> <M-/>
map  <silent> <buffer> <C-c>rd :RopeShowDoc<CR>
