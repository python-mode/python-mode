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

    " OPTION: g:pymode_rope_auto_project -- bool. Auto open ropeproject
    call helpers#SafeVar("g:pymode_rope_auto_project", 1)

    " OPTION: g:pymode_rope_enable_autoimport -- bool. Enable autoimport
    call helpers#SafeVar("g:pymode_rope_enable_autoimport", 1)

    " OPTION: g:pymode_rope_autoimport_underlines -- bool.
    call helpers#SafeVar("g:pymode_rope_autoimport_underlineds", 0)

    " OPTION: g:pymode_rope_codeassist_maxfiles -- bool.
    call helpers#SafeVar("g:pymode_rope_codeassist_maxfixes", 10)

    " OPTION: g:pymode_rope_sorted_completions -- bool.
    call helpers#SafeVar("g:pymode_rope_sorted_completions", 1)

    " OPTION: g:pymode_rope_extended_complete -- bool.
    call helpers#SafeVar("g:pymode_rope_extended_complete", 0)

    " OPTION: g:pymode_rope_autoimport_modules -- array.
    call helpers#SafeVar("g:pymode_rope_autoimport_modules", ["os","shutil","datetime"])

    " OPTION: g:pymode_rope_confirm_saving -- bool.
    call helpers#SafeVar("g:pymode_rope_confirm_saving", 1)

    " OPTION: g:pymode_rope_global_prefix -- string.
    call helpers#SafeVar("g:pymode_rope_global_prefix", "<C-c>r")

    " OPTION: g:pymode_rope_local_prefix -- string.
    call helpers#SafeVar("g:pymode_rope_local_prefix", "<C-x>p")

    " OPTION: g:pymode_rope_vim_completion -- bool.
    call helpers#SafeVar("g:pymode_rope_vim_completion", 1)

    " OPTION: g:pymode_rope_guess_project -- bool.
    call helpers#SafeVar("g:pymode_rope_guess_project", 1)

    " DESC: Init Rope
    py import ropevim

    fun! RopeOmni(findstart, base) "{{{
        call RopeCodeAssistInsertMode()
        return ""
    endfunction "}}}

endif

" DESC: Set keys
imap <silent> <buffer> <Nul> <M-/>
imap <silent> <buffer> <C-Space> <M-/>
map  <silent> <buffer> <C-c>rd :RopeShowDoc<CR>
