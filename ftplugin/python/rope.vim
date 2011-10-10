if !helpers#SafeVar("g:rope_loaded", 1)
    py import ropevim

    " RopeVim settings
    let g:ropevim_codeassist_maxfixes=10
    let g:ropevim_guess_project=1
    let g:ropevim_vim_completion=1
    let g:ropevim_enable_autoimport=1
    let g:ropevim_autoimport_modules = ["os", "shutil"]
endif

" Keys
imap <silent> <buffer> <Nul> <M-/>
imap <silent> <buffer> <C-Space> <M-/>
map  <silent> <buffer> <C-c>rd :RopeShowDoc<CR>
