" DESC: Set scriptname
let g:scriptname = expand("<sfile>:t")

" OPTION: g:pymode_rope -- bool. Load rope plugin
call helpers#SafeVar("g:pymode_rope", 1)

" DESC: Disable script loading
if g:pymode_rope == 0
    finish
endif

" DESC: Check python support
if !has('python')
    echoerr s:scriptname . " required vim compiled with +python."
    finish
endif

if !helpers#SafeVar("g:rope_loaded", 1)
    py import ropevim

    " RopeVim settings
    let g:ropevim_codeassist_maxfixes=10
    let g:ropevim_guess_project=1
    let g:ropevim_vim_completion=1
    let g:ropevim_enable_autoimport=1
    let g:ropevim_autoimport_modules = ["os", "shutil"]
endif

" DESC: Set keys
imap <silent> <buffer> <Nul> <M-/>
imap <silent> <buffer> <C-Space> <M-/>
map  <silent> <buffer> <C-c>rd :RopeShowDoc<CR>
