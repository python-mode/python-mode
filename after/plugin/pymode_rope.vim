" OPTION: g:pymode_rope -- bool. Load rope plugin
call helpers#SafeVar("g:pymode_rope", 1)

" DESC: Disable script loading
if !g:pymode_rope || !g:pymode
    let g:pymode_rope = 0
    finish
endif

" OPTION: g:pymode_rope_auto_project -- bool. Auto open ropeproject
call helpers#SafeVar("g:pymode_rope_auto_project", 1)

" OPTION: g:pymode_rope_enable_autoimport -- bool. Enable autoimport
call helpers#SafeVar("g:pymode_rope_enable_autoimport", 1)

" OPTION: g:pymode_rope_autoimport_generate -- bool.
call helpers#SafeVar("g:pymode_rope_autoimport_generate", 1)

" OPTION: g:pymode_rope_autoimport_underlines -- bool.
call helpers#SafeVar("g:pymode_rope_autoimport_underlineds", 0)

" OPTION: g:pymode_rope_codeassist_maxfiles -- bool.
call helpers#SafeVar("g:pymode_rope_codeassist_maxfixes", 10)

" OPTION: g:pymode_rope_sorted_completions -- bool.
call helpers#SafeVar("g:pymode_rope_sorted_completions", 1)

" OPTION: g:pymode_rope_extended_complete -- bool.
call helpers#SafeVar("g:pymode_rope_extended_complete", 1)

" OPTION: g:pymode_rope_autoimport_modules -- array.
call helpers#SafeVar("g:pymode_rope_autoimport_modules", ["os","shutil","datetime"])

" OPTION: g:pymode_rope_confirm_saving -- bool.
call helpers#SafeVar("g:pymode_rope_confirm_saving", 1)

" OPTION: g:pymode_rope_global_prefix -- string.
call helpers#SafeVar("g:pymode_rope_global_prefix", "<C-x>p")

" OPTION: g:pymode_rope_local_prefix -- string.
call helpers#SafeVar("g:pymode_rope_local_prefix", "<C-c>r")

" OPTION: g:pymode_rope_vim_completion -- bool.
call helpers#SafeVar("g:pymode_rope_vim_completion", 1)

" OPTION: g:pymode_rope_guess_project -- bool.
call helpers#SafeVar("g:pymode_rope_guess_project", 1)

" OPTION: g:pymode_rope_goto_def_newwin -- bool.
call helpers#SafeVar("g:pymode_rope_goto_def_newwin", 0)

" DESC: Init Rope
py import ropevim

fun! RopeCodeAssistInsertMode() "{{{
    call RopeCodeAssist()
    return ""
endfunction "}}}

fun! RopeLuckyAssistInsertMode() "{{{
    call RopeLuckyAssist()
    return ""
endfunction "}}}

fun! RopeOmni(findstart, base) "{{{
    " TODO: Fix omni
    if a:findstart == 1
        let start = col('.') - 1
        return start
    else
        call RopeOmniComplete()
        return g:pythoncomplete_completions
    endif
endfunction "}}}

" Rope menu
menu <silent> Rope.Autoimport :RopeAutoImport<CR>
menu <silent> Rope.ChangeSignature :RopeChangeSignature<CR>
menu <silent> Rope.CloseProject :RopeCloseProject<CR>
menu <silent> Rope.GenerateAutoImportCache :RopeGenerateAutoimportCache<CR>
menu <silent> Rope.ExtractVariable :RopeExtractVariable<CR>
menu <silent> Rope.ExtractMethod :RopeExtractMethod<CR>
menu <silent> Rope.Inline :RopeInline<CR>
menu <silent> Rope.IntroduceFactory :RopeIntroduceFactory<CR>
menu <silent> Rope.FindFile :RopeFindFile<CR>
menu <silent> Rope.OpenProject :RopeOpenProject<CR>
menu <silent> Rope.Move :RopeMove<CR>
menu <silent> Rope.MoveCurrentModule :RopeMoveCurrentModule<CR>
menu <silent> Rope.ModuleToPackage :RopeModuleToPackage<CR>
menu <silent> Rope.Redo :RopeRedo<CR>
menu <silent> Rope.Rename :RopeRename<CR>
menu <silent> Rope.RenameCurrentModule :RopeRenameCurrentModule<CR>
menu <silent> Rope.Restructure :RopeRestructure<CR>
menu <silent> Rope.Undo :RopeUndo<CR>
menu <silent> Rope.UseFunction :RopeUseFunction<CR>
