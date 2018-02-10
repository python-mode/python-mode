if !g:pymode || pymode#default('b:pymode', 1)
    finish
endif

if g:pymode_python == 'disable'

    if g:pymode_warning
        call pymode#error("Pymode requires vim compiled with +python. Most of features will be disabled.")
    endif

    finish

else


let b:pymode_modified = &modified

" Init paths
if !pymode#default('g:pymode_init', 1)

        call pymode#init(expand('<sfile>:p:h:h:h'), g:pymode_paths)
        call pymode#virtualenv#init()
        call pymode#breakpoint#init()

        PymodePython from pymode.utils import patch_paths
        PymodePython patch_paths()

    endif

endif

command! -buffer -nargs=1 PymodeVirtualenv call pymode#virtualenv#activate(<args>)

" Setup events for pymode
au! pymode BufWritePre <buffer> call pymode#buffer_pre_write()
au! pymode BufWritePost <buffer> call pymode#buffer_post_write()

" Run python code
if g:pymode_run

    command! -buffer -nargs=0 -range=% PymodeRun call pymode#run#code_run(<f-line1>, <f-line2>)

    exe "nnoremap <silent> <buffer> " g:pymode_run_bind ":PymodeRun<CR>"
    exe "vnoremap <silent> <buffer> " g:pymode_run_bind ":PymodeRun<CR>"

endif

" Add/remove breakpoints
if g:pymode_breakpoint

    exe "nnoremap <silent> <buffer> " g:pymode_breakpoint_bind ":call pymode#breakpoint#operate(line('.'))<CR>"

endif

" Python folding
if g:pymode_folding

    setlocal foldmethod=expr
    setlocal foldexpr=pymode#folding#expr(v:lnum)
    setlocal foldtext=pymode#folding#text()

endif

" Remove unused whitespaces
if g:pymode_trim_whitespaces
    au BufWritePre <buffer> call pymode#trim_whitespaces()
endif

" Custom options
if g:pymode_options
    setlocal complete+=t
    setlocal formatoptions-=t
    if v:version > 702 && !&relativenumber
        setlocal number
    endif
    setlocal nowrap
    exe "setlocal textwidth=" . g:pymode_options_max_line_length
    if g:pymode_options_colorcolumn && exists('+colorcolumn')
        setlocal colorcolumn=+1
    endif
    setlocal commentstring=#%s
    setlocal define=^\s*\\(def\\\\|class\\)
endif

if g:pymode_lint

    command! -buffer -nargs=0 PymodeLintAuto :call pymode#lint#auto()
    command! -buffer -nargs=0 PymodeLintToggle :call pymode#lint#toggle()
    command! -buffer -nargs=0 PymodeLint :call pymode#lint#check()

    if v:version > 703 || (v:version == 703 && has('patch544'))
        au! QuitPre <buffer> call pymode#quit()
    else
        au! pymode BufWinLeave * silent! lclose
    endif

    let b:pymode_error_line = -1

    if g:pymode_lint_on_fly
        au! pymode InsertLeave <buffer> PymodeLint
    endif

    if g:pymode_lint_message
        au! pymode CursorMoved <buffer>
        au! pymode CursorMoved <buffer> call pymode#lint#show_errormessage()
    endif

    " Disabled for current release
    if g:pymode_lint_async
        " let &l:updatetime = g:pymode_lint_async_updatetime
        " au! BufEnter <buffer> call pymode#lint#start()
        " au! BufLeave <buffer> call pymode#lint#stop()
    endif

endif

" Show python documentation
if g:pymode_doc

    " Set commands
    command! -buffer -nargs=1 PymodeDoc call pymode#doc#show("<args>")

    " Set keys
    exe "nnoremap <silent> <buffer> " g:pymode_doc_bind ":call pymode#doc#find()<CR>"
    exe "vnoremap <silent> <buffer> " g:pymode_doc_bind ":<C-U>call pymode#doc#show(@*)<CR>"

endif

" Rope support
if g:pymode_rope

    if g:pymode_rope_goto_definition_bind != ""
        exe "noremap <silent> <buffer> " . g:pymode_rope_goto_definition_bind . " :call pymode#rope#goto_definition()<CR>"
    endif
    if g:pymode_rope_show_doc_bind != ""
        exe "noremap <silent> <buffer> " . g:pymode_rope_show_doc_bind . " :call pymode#rope#show_doc()<CR>"
    endif
    if g:pymode_rope_find_it_bind != ""
        exe "noremap <silent> <buffer> " . g:pymode_rope_find_it_bind . " :call pymode#rope#find_it()<CR>"
    endif
    if g:pymode_rope_organize_imports_bind != ""
        exe "noremap <silent> <buffer> " . g:pymode_rope_organize_imports_bind . " :call pymode#rope#organize_imports()<CR>"
    endif

    if g:pymode_rope_rename_bind != ""
        exe "noremap <silent> <buffer> " . g:pymode_rope_rename_bind . " :call pymode#rope#rename()<CR>"
    endif

    if g:pymode_rope_rename_module_bind != ""
        exe "noremap <silent> <buffer> " . g:pymode_rope_rename_module_bind . " :call pymode#rope#rename_module()<CR>"
    endif

    if g:pymode_rope_extract_method_bind != ""
        exe "vnoremap <silent> <buffer> " . g:pymode_rope_extract_method_bind . " :call pymode#rope#extract_method()<CR>"
    endif

    if g:pymode_rope_extract_variable_bind != ""
        exe "vnoremap <silent> <buffer> " . g:pymode_rope_extract_variable_bind . " :call pymode#rope#extract_variable()<CR>"
    endif

    if g:pymode_rope_inline_bind != ""
        exe "noremap <silent> <buffer> " . g:pymode_rope_inline_bind . " :call pymode#rope#inline()<CR>"
    endif

    if g:pymode_rope_move_bind != ""
        exe "noremap <silent> <buffer> " . g:pymode_rope_move_bind . " :call pymode#rope#move()<CR>"
    endif

    if g:pymode_rope_change_signature_bind != ""
        exe "noremap <silent> <buffer> " . g:pymode_rope_change_signature_bind . " :call pymode#rope#signature()<CR>"
    endif

    if g:pymode_rope_use_function_bind != ""
        exe "noremap <silent> <buffer> " . g:pymode_rope_use_function_bind . " :call pymode#rope#use_function()<CR>"
    endif

    if g:pymode_rope_generate_function_bind != ""
        exe "noremap <silent> <buffer> " . g:pymode_rope_generate_function_bind . " :call pymode#rope#generate_function()<CR>"
    endif

    if g:pymode_rope_generate_package_bind != ""
        exe "noremap <silent> <buffer> " . g:pymode_rope_generate_package_bind . " :call pymode#rope#generate_package()<CR>"
    endif

    if g:pymode_rope_generate_class_bind != ""
        exe "noremap <silent> <buffer> " . g:pymode_rope_generate_class_bind . " :call pymode#rope#generate_class()<CR>"
    endif

    if g:pymode_rope_module_to_package_bind != ""
        exe "noremap <silent> <buffer> " . g:pymode_rope_module_to_package_bind . " :call pymode#rope#module_to_package()<CR>"
    endif

    if g:pymode_rope_autoimport_bind != ""
        exe "noremap <silent> <buffer> " . g:pymode_rope_autoimport_bind . " :PymodeRopeAutoImport<CR>"
    endif

    if g:pymode_rope_completion && g:pymode_rope_complete_on_dot
        inoremap <silent> <buffer> . .<C-R>=pymode#rope#complete_on_dot()<CR>
    endif

    command! -buffer -nargs=? PymodeRopeNewProject call pymode#rope#new(<f-args>)
    command! -buffer PymodeRopeUndo call pymode#rope#undo()
    command! -buffer PymodeRopeRedo call pymode#rope#redo()
    command! -buffer PymodeRopeRenameModule call pymode#rope#rename_module()
    command! -buffer PymodeRopeModuleToPackage call pymode#rope#module_to_package()
    command! -buffer PymodeRopeRegenerate call pymode#rope#regenerate()

    if g:pymode_rope_autoimport
        command! -buffer PymodeRopeAutoImport call pymode#rope#autoimport(expand('<cword>'))
    endif

endif


if g:pymode_debug
    " Redefine functions to be debugged here functions here.

    " NOTE: The redraw seems to be necessary to force messages to get echoed to
    " the screen. See:
    " https://groups.google.com/forum/#!topic/vim_use/EfcXOjq_rKE
    " for details.
    " silent! redraw!
    " TODO: when loading with 'vim -u ./debug.vim' the messages shown in vim
    " are unduly cleared. Need a fix.

    " Start debbuging environment. {{{
    if ! &verbosefile
        " Get a system independent temporary filename. The 'marker' variable is
        " used to get rid of a null character getting inserted at position.
        " substitute() was not able to remove it.
        " TODO: see https://superuser.com/questions/935574/get-rid-of-null-character-in-vim-variable
        let g:pymode_debug_tempfile=matchstr(
            \ execute(
            \ g:pymode_python
            \ . " import os;import tempfile; marker='|';"
            \ . " print(marker, tempfile.gettempdir(), os.sep, "
            \ .        "'pymode_debug_file.txt', marker, sep='', end='')"),
            \ '|\zs.*\ze|')
        execute "set verbosefile="  . g:pymode_debug_tempfile
    endif
    call pymode#debug('Starting debug on: '
                      \ . strftime("\%Y-\%m-\%d \%H:\%M:\%S")
                      \ . ' with file ' . &verbosefile)
    " }}}
    " Redefine folding expression. {{{
    if g:pymode_folding
        setlocal foldexpr=pymode#debug#foldingexpr(v:lnum)
    endif
    call pymode#debug#sysinfo()
    " }}}
    " Define auto commands for vim. {{{
    augroup augroup_save_issue_commands
        autocmd!
        autocmd VimLeave *.py | call pymode#debug('Session history:') | silent! history
    augroup END
    " }}}

    endif
