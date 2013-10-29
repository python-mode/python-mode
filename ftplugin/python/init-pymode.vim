if pymode#Default('g:pymode_init', 1)
    finish
endif

call pymode#Default('g:pymode_test', 0)

let g:pymode_version = "0.6.19"

com! PymodeVersion echomsg "Current python-mode version: " . g:pymode_version

" OPTION: g:pymode -- bool. Run pymode.
if pymode#Default('g:pymode', 1) || !g:pymode
    " DESC: Disable script loading
    finish
endif

" DESC: Check python support
if !has('python') && !has('python3')
    let g:pymode_virtualenv = 0
    let g:pymode_path       = 0
    let g:pymode_lint       = 0
    let g:pymode_doc        = 0
    let g:pymode_breakpoint = 0
    let g:pymode_rope       = 0
    let g:pymode_run        = 0
endif

if has('python')
    command! -nargs=1 Python python <args>
elseif has('python3')
    command! -nargs=1 Python python3 <args>
end

" Virtualenv {{{

if !pymode#Default("g:pymode_virtualenv", 1) || g:pymode_virtualenv

    call pymode#Default("g:pymode_virtualenv_enabled", [])

    " Add virtualenv paths
    call pymode#virtualenv#Activate()

endif

" }}}


" DESC: Add pymode's pylibs to sys.path {{{
if !pymode#Default('g:pymode_path', 1) || g:pymode_path

    call pymode#Default('g:pymode_paths', [])
    call pymode#path#Activate(expand("<sfile>:p:h:h:h"))

endif " }}}


" Lint {{{

if !pymode#Default("g:pymode_lint", 1) || g:pymode_lint

    let g:qf_list = []
    let g:pymode_lint_buffer = 0

    " OPTION: g:pymode_lint_write -- bool. Check code every save.
    call pymode#Default("g:pymode_lint_write", 1)

    " OPTION: g:pymode_lint_async -- bool. Run a checkers asynchronously 
    call pymode#Default("g:pymode_lint_async", 1)

    " OPTION: g:pymode_lint_onfly -- bool. Check code every save.
    call pymode#Default("g:pymode_lint_onfly", 0)

    " OPTION: g:pymode_lint_message -- bool. Show current line error message
    call pymode#Default("g:pymode_lint_message", 1)

    " OPTION: g:pymode_lint_checker -- str. Choices are: pylint, pyflakes, pep8, mccabe
    call pymode#Default("g:pymode_lint_checker", "pyflakes,pep8,mccabe")

    " OPTION: g:pymode_lint_config -- str. Path to pylint config file
    call pymode#Default("g:pymode_lint_config", $HOME . "/.pylintrc")

    " OPTION: g:pymode_lint_cwindow -- bool. Auto open cwindow if errors find
    call pymode#Default("g:pymode_lint_cwindow", 1)

    " OPTION: g:pymode_lint_jump -- int. Jump on first error.
    call pymode#Default("g:pymode_lint_jump", 0)

    " OPTION: g:pymode_lint_hold -- int. Hold cursor on current window when
    " quickfix open
    call pymode#Default("g:pymode_lint_hold", 0)

    " OPTION: g:pymode_lint_minheight -- int. Minimal height of pymode lint window
    call pymode#Default("g:pymode_lint_minheight", 3)

    " OPTION: g:pymode_lint_maxheight -- int. Maximal height of pymode lint window
    call pymode#Default("g:pymode_lint_maxheight", 6)

    " OPTION: g:pymode_lint_ignore -- string. Skip errors and warnings (e.g. E4,W)
    call pymode#Default("g:pymode_lint_ignore", "")

    " OPTION: g:pymode_lint_select -- string. Select errors and warnings (e.g. E4,W)
    call pymode#Default("g:pymode_lint_select", "")

    " OPTION: g:pymode_lint_mccabe_complexity -- int. Maximum allowed complexity
    call pymode#Default("g:pymode_lint_mccabe_complexity", 8)

    " OPTION: g:pymode_lint_signs_always_visible -- bool. Always show the
    " errors ruller, even if there's no errors.
    call pymode#Default("g:pymode_lint_signs_always_visible", 0)

    " OPTION: g:pymode_lint_todo_symbol -- string. Todo symbol.
    call pymode#Default("g:pymode_lint_todo_symbol", "WW")

    " OPTION: g:pymode_lint_comment_symbol -- string. Comment symbol.
    call pymode#Default("g:pymode_lint_comment_symbol", "CC")

    " OPTION: g:pymode_lint_visual_symbol -- string. Visual symbol.
    call pymode#Default("g:pymode_lint_visual_symbol", "RR")

    " OPTION: g:pymode_lint_error_symbol -- string. Error symbol.
    call pymode#Default("g:pymode_lint_error_symbol", "EE")

    " OPTION: g:pymode_lint_info_symbol -- string. Info symbol.
    call pymode#Default("g:pymode_lint_info_symbol", "II")

    " OPTION: g:pymode_lint_pyflakes_symbol -- string. PyFlakes' info symbol.
    call pymode#Default("g:pymode_lint_pyflakes_symbol", "FF")

    " OPTION: g:pymode_lint_signs -- bool. Place error signs
    if (!pymode#Default("g:pymode_lint_signs", 1) || g:pymode_lint_signs) && has('signs')

        " DESC: Signs definition
        execute 'sign define PymodeW text=' . g:pymode_lint_todo_symbol     . " texthl=Todo"
        execute 'sign define PymodeC text=' . g:pymode_lint_comment_symbol  . " texthl=Comment"
        execute 'sign define PymodeR text=' . g:pymode_lint_visual_symbol   . " texthl=Visual"
        execute 'sign define PymodeE text=' . g:pymode_lint_error_symbol    . " texthl=Error"
        execute 'sign define PymodeI text=' . g:pymode_lint_info_symbol     . " texthl=Info"
        execute 'sign define PymodeF text=' . g:pymode_lint_pyflakes_symbol . " texthl=Info"

        if !pymode#Default("g:pymode_lint_signs_always_visible", 0) || g:pymode_lint_signs_always_visible
            " Show the sign's ruller if asked for, even it there's no error to show
            sign define __dummy__
            autocmd BufRead,BufNew * call RopeShowSignsRulerIfNeeded()
        endif

    endif

    " DESC: Set default pylint configuration
    if !filereadable(g:pymode_lint_config)
        let g:pymode_lint_config = expand("<sfile>:p:h:h:h") . "/pylint.ini"
    endif

    Python from pymode import queue

    au VimLeavePre * Python queue.stop_queue()

endif

" }}}


" Documentation {{{

if !pymode#Default("g:pymode_doc", 1) || g:pymode_doc

    " OPTION: g:pymode_doc_key -- string. Key for show python documantation.
    call pymode#Default("g:pymode_doc_key", "K")

endif

" }}}


" Breakpoints {{{

if !pymode#Default("g:pymode_breakpoint", 1) || g:pymode_breakpoint

    if !pymode#Default("g:pymode_breakpoint_cmd", "import pdb; pdb.set_trace()  # XXX BREAKPOINT")  && has("python")

        call pymode#breakpoint#SearchDebuger()

    endif

    " OPTION: g:pymode_breakpoint_key -- string. Key for set/unset breakpoint.
    call pymode#Default("g:pymode_breakpoint_key", "<leader>b")

endif

" }}}


" Execution {{{

if !pymode#Default("g:pymode_run", 1) || g:pymode_run

    " OPTION: g:pymode_doc_key -- string. Key for show python documentation.
    call pymode#Default("g:pymode_run_key", "<leader>r")

endif

" }}}


" Rope {{{

if !pymode#Default("g:pymode_rope", 1) || g:pymode_rope

    " OPTION: g:pymode_rope_autocomplete_key -- str. Key for the rope
    " autocompletion.
    call pymode#Default("g:pymode_rope_autocomplete_map", "<C-Space>")

    " OPTION: g:pymode_rope_auto_project -- bool. Auto create ropeproject
    call pymode#Default("g:pymode_rope_auto_project", 1)

    " OPTION: g:pymode_rope_auto_project_open -- bool.
    " Auto open existing projects, ie, if the current directory has a
    " `.ropeproject` subdirectory.
    call pymode#Default("g:pymode_rope_auto_project_open", 1)

    " OPTION: g:pymode_rope_enable_autoimport -- bool. Enable autoimport
    call pymode#Default("g:pymode_rope_enable_autoimport", 1)

    " OPTION: g:pymode_rope_autoimport_generate -- bool.
    call pymode#Default("g:pymode_rope_autoimport_generate", 1)

    " OPTION: g:pymode_rope_autoimport_underlines -- bool.
    call pymode#Default("g:pymode_rope_autoimport_underlineds", 0)

    " OPTION: g:pymode_rope_codeassist_maxfiles -- bool.
    call pymode#Default("g:pymode_rope_codeassist_maxfixes", 10)

    " OPTION: g:pymode_rope_sorted_completions -- bool.
    call pymode#Default("g:pymode_rope_sorted_completions", 1)

    " OPTION: g:pymode_rope_extended_complete -- bool.
    call pymode#Default("g:pymode_rope_extended_complete", 1)

    " OPTION: g:pymode_rope_autoimport_modules -- array.
    call pymode#Default("g:pymode_rope_autoimport_modules", ["os","shutil","datetime"])

    " OPTION: g:pymode_rope_confirm_saving -- bool.
    call pymode#Default("g:pymode_rope_confirm_saving", 1)

    " OPTION: g:pymode_rope_global_prefix -- string.
    call pymode#Default("g:pymode_rope_global_prefix", "<C-x>p")

    " OPTION: g:pymode_rope_local_prefix -- string.
    call pymode#Default("g:pymode_rope_local_prefix", "<C-c>r")

    " OPTION: g:pymode_rope_short_prefix -- string.
    call pymode#Default("g:pymode_rope_short_prefix", "<C-c>")

    " OPTION: g:pymode_rope_vim_completion -- bool.
    call pymode#Default("g:pymode_rope_vim_completion", 1)

    " OPTION: g:pymode_rope_guess_project -- bool.
    call pymode#Default("g:pymode_rope_guess_project", 1)

    " OPTION: g:pymode_rope_goto_def_newwin -- str ('new', 'vnew', '').
    call pymode#Default("g:pymode_rope_goto_def_newwin", "")

    " OPTION: g:pymode_rope_always_show_complete_menu -- bool.
    call pymode#Default("g:pymode_rope_always_show_complete_menu", 0)

    " DESC: Init Rope
    Python import ropevim

    fun! RopeCodeAssistInsertMode() "{{{
        call RopeCodeAssist()
        return ""
    endfunction "}}}

    fun! RopeOpenExistingProject() "{{{
        if isdirectory(getcwd() . '/.ropeproject')
            " In order to pass it the quiet kwarg I need to open the project
            " using python and not vim, which should be no major issue
            Python ropevim._interface.open_project(quiet=True)
            return ""
        endif
    endfunction "}}}

    fun! RopeLuckyAssistInsertMode() "{{{
        call RopeLuckyAssist()
        return ""
    endfunction "}}}

    fun! RopeOmni(findstart, base) "{{{
        if a:findstart
            Python ropevim._interface._find_start()
            return g:pymode_offset
        else
            call RopeOmniComplete()
            return g:pythoncomplete_completions
        endif
    endfunction "}}}

    fun! RopeShowSignsRulerIfNeeded() "{{{
        if &ft == 'python'
            execute printf('silent! sign place 1 line=1 name=__dummy__ file=%s', expand("%:p"))
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

    if !pymode#Default("g:pymode_rope_auto_project_open", 1) || g:pymode_rope_auto_project_open
        call RopeOpenExistingProject()
    endif

endif

" }}}


" OPTION: g:pymode_folding -- bool. Enable python-mode folding for pyfiles.
call pymode#Default("g:pymode_folding", 1)

" OPTION: g:pymode_syntax -- bool. Enable python-mode syntax for pyfiles.
call pymode#Default("g:pymode_syntax", 1)

" OPTION: g:pymode_indent -- bool. Enable/Disable pymode PEP8 indentation
call pymode#Default("g:pymode_indent", 1)

" OPTION: g:pymode_utils_whitespaces -- bool. Remove unused whitespaces on save
call pymode#Default("g:pymode_utils_whitespaces", 1)

" OPTION: g:pymode_options -- bool. To set some python options.
call pymode#Default("g:pymode_options", 1)

" OPTION: g:pymode_updatetime -- int. Set updatetime for async pymode's operation
call pymode#Default("g:pymode_updatetime", 1000)

" OPTION: g:pymode_modeline -- int. Support pymode modeline.
if pymode#Default('g:pymode_modeline', 1) || !g:pymode_modeline
    au BufRead *.py call pymode#Modeline()
endif

" vim: fdm=marker:fdl=0
