" vi: fdl=1
let g:pymode_version = "0.8.1"

com! PymodeVersion echomsg "Current python-mode version: " . g:pymode_version
com! PymodeTroubleshooting call pymode#troubleshooting#test()

" Enable pymode by default :)
call pymode#default('g:pymode', 1)
call pymode#default('g:pymode_debug', 0)

" DESC: Disable script loading
if !g:pymode || &cp
    finish
endif

" Pymode needs
filetype plugin on

" OPTIONS: {{{

" Vim Python interpreter. Set to 'disable' for remove python features.
call pymode#default('g:pymode_python', '')

" Disable pymode warnings
call pymode#default('g:pymode_warning', 1)

" Additional python paths
call pymode#default('g:pymode_paths', [])

" Python documentation support
call pymode#default('g:pymode_doc', 1)
call pymode#default('g:pymode_doc_bind', 'K')

" Enable/Disable pymode PEP8 indentation
call pymode#default("g:pymode_indent", 1)

" Enable/disable pymode folding for pyfiles.
call pymode#default("g:pymode_folding", 1)
" Maximum file length to check for nested class/def statements
call pymode#default("g:pymode_folding_nest_limit", 1000)
" Change for folding customization (by example enable fold for 'if', 'for')
call pymode#default("g:pymode_folding_regex", '^\s*\%(class\|def\) \w\+')

" Enable/disable python motion operators
call pymode#default("g:pymode_motion", 1)

" Auto remove unused whitespaces on save
call pymode#default("g:pymode_trim_whitespaces", 1)

" Set recomended python options
call pymode#default("g:pymode_options", 1)
call pymode#default("g:pymode_options_max_line_length", 80)
call pymode#default("g:pymode_options_colorcolumn", 1)

" Minimal height of pymode quickfix window
call pymode#default('g:pymode_quickfix_maxheight', 6)

" Maximal height of pymode quickfix window
call pymode#default('g:pymode_quickfix_minheight', 3)

" LOAD VIRTUALENV {{{
"
" Enable virtualenv support
call pymode#default('g:pymode_virtualenv', 1)

" Get path to virtualenv (by default take from shell)
call pymode#default('g:pymode_virtualenv_path', $VIRTUAL_ENV)

" Service variable (don't set it manually)
call pymode#default('g:pymode_virtualenv_enabled', '')

" }}}

" RUN PYTHON {{{
"
" Enable code running support
call pymode#default('g:pymode_run', 1)

" Key's map for run python code
call pymode#default('g:pymode_run_bind', '<leader>r')

" }}}

" CHECK CODE {{{
"
" Code checking
call pymode#default('g:pymode_lint', 1)

" Check code asynchronously
call pymode#default('g:pymode_lint_async', 1)
call pymode#default('g:pymode_lint_async_updatetime', 1000)

" Check code every save if file has been modified
call pymode#default("g:pymode_lint_on_write", 1)

" Check code every save (every)
call pymode#default("g:pymode_lint_unmodified", 0)

" Check code on fly
call pymode#default("g:pymode_lint_on_fly", 0)

" Show message about error in command line
call pymode#default("g:pymode_lint_message", 1)

" Choices are: pylint, pyflakes, pep8, mccabe
call pymode#default("g:pymode_lint_checkers", ['pyflakes', 'pep8', 'mccabe'])

" Skip errors and warnings (e.g. E4,W)
call pymode#default("g:pymode_lint_ignore", "")

" Select errors and warnings (e.g. E4,W)
call pymode#default("g:pymode_lint_select", "")

" Auto open cwindow if any errors has been finded
call pymode#default("g:pymode_lint_cwindow", 1)

" If not emply, errors will be sort by defined relevance
" E.g. let g:pymode_lint_sort = ['E', 'C', 'I']  " Errors first 'E',
" after them 'C' and ...
call pymode#default("g:pymode_lint_sort", [])

" Place error signs
call pymode#default("g:pymode_lint_signs", 1)

" Symbol's definitions
call pymode#default("g:pymode_lint_todo_symbol", "WW")
call pymode#default("g:pymode_lint_docs_symbol", "DD")
call pymode#default("g:pymode_lint_comment_symbol", "CC")
call pymode#default("g:pymode_lint_visual_symbol", "RR")
call pymode#default("g:pymode_lint_error_symbol", "EE")
call pymode#default("g:pymode_lint_info_symbol", "II")
call pymode#default("g:pymode_lint_pyflakes_symbol", "FF")

" Code checkers options
call pymode#default("g:pymode_lint_options_pep8",
    \ {'max_line_length': g:pymode_options_max_line_length})

call pymode#default("g:pymode_lint_options_pylint",
    \ {'max-line-length': g:pymode_options_max_line_length})

call pymode#default("g:pymode_lint_options_mccabe",
    \ {'complexity': 12})

call pymode#default("g:pymode_lint_options_pep257", {})
call pymode#default("g:pymode_lint_options_pyflakes", { 'builtins': '_' })


" }}}

" SET/UNSET BREAKPOINTS {{{
"

" Create/remove breakpoints
call pymode#default('g:pymode_breakpoint', 1)

" Key's map for add/remove breakpoint
call pymode#default('g:pymode_breakpoint_bind', '<leader>b')

" Default pattern for making breakpoints. Leave this empty for auto search available debuggers (pdb, ipdb, ...)
call pymode#default('g:pymode_breakpoint_cmd', '')

" }}}

" ROPE (refactoring, codeassist) {{{
"
" Rope support
call pymode#default('g:pymode_rope', 1)

" System plugin variable
call pymode#default('g:pymode_rope_current', '')

" Configurable rope project root
call pymode#default('g:pymode_rope_project_root', '')

" Configurable rope project folder (always relative to project root)
call pymode#default('g:pymode_rope_ropefolder', '.ropeproject')

" If project hasnt been finded in current working directory, look at parents directory
call pymode#default('g:pymode_rope_lookup_project', 0)

" Enable Rope completion
call pymode#default('g:pymode_rope_completion', 1)

" Complete keywords from not imported modules (could make completion slower)
" Enable autoimport used modules
call pymode#default('g:pymode_rope_autoimport', 1)

" Offer to import object after complete (if that not be imported before)
call pymode#default('g:pymode_rope_autoimport_import_after_complete', 0)

" Autoimported modules
call pymode#default('g:pymode_rope_autoimport_modules', ['os', 'shutil', 'datetime'])

" Bind keys to autoimport module for object under cursor
call pymode#default('g:pymode_rope_autoimport_bind', '<C-c>ra')

" Automatic completion on dot
call pymode#default('g:pymode_rope_complete_on_dot', 1)

" Bind keys for autocomplete (leave empty for disable)
call pymode#default('g:pymode_rope_completion_bind', '<C-Space>')

" Bind keys for goto definition (leave empty for disable)
call pymode#default('g:pymode_rope_goto_definition_bind', '<C-c>g')

" set command for open definition (e, new, vnew)
call pymode#default('g:pymode_rope_goto_definition_cmd', 'new')

" Bind keys for show documentation (leave empty for disable)
call pymode#default('g:pymode_rope_show_doc_bind', '<C-c>d')

" Bind keys for find occurencies (leave empty for disable)
call pymode#default('g:pymode_rope_find_it_bind', '<C-c>f')

" Bind keys for organize imports (leave empty for disable)
call pymode#default('g:pymode_rope_organize_imports_bind', '<C-c>ro')

" Bind keys for rename variable/method/class in the project (leave empty for disable)
call pymode#default('g:pymode_rope_rename_bind', '<C-c>rr')

" Bind keys for rename module
call pymode#default('g:pymode_rope_rename_module_bind', '<C-c>r1r')

" Bind keys for convert module to package
call pymode#default('g:pymode_rope_module_to_package_bind', '<C-c>r1p')

" Creates a new function or method (depending on the context) from the selected lines
call pymode#default('g:pymode_rope_extract_method_bind', '<C-c>rm')

" Creates a variable from the selected lines
call pymode#default('g:pymode_rope_extract_variable_bind', '<C-c>rl')

" Inline refactoring
call pymode#default('g:pymode_rope_inline_bind', '<C-c>ri')

" Move refactoring
call pymode#default('g:pymode_rope_move_bind', '<C-c>rv')

" Generate function
call pymode#default('g:pymode_rope_generate_function_bind', '<C-c>rnf')

" Generate class
call pymode#default('g:pymode_rope_generate_class_bind', '<C-c>rnc')

" Generate package
call pymode#default('g:pymode_rope_generate_package_bind', '<C-c>rnp')

" Change signature
call pymode#default('g:pymode_rope_change_signature_bind', '<C-c>rs')

" Tries to find the places in which a function can be used and changes the
" code to call it instead
call pymode#default('g:pymode_rope_use_function_bind', '<C-c>ru')

" Regenerate project cache on every save
call pymode#default('g:pymode_rope_regenerate_on_write', 1)

" }}}

" }}}

" Prepare to plugin loading
if &compatible
    set nocompatible
endif
filetype plugin on

" Disable python-related functionality
" let g:pymode_python = 'disable'
" let g:pymode_python = 'python3'

" UltiSnips Fixes
if !len(g:pymode_python)
    if exists('g:_uspy') && g:_uspy == ':py'
        let g:pymode_python = 'python'
    elseif exists('g:_uspy') && g:_uspy == ':py3'
        let g:pymode_python = 'python3'
    elseif has("python")
        let g:pymode_python = 'python'
    elseif has("python3")
        let g:pymode_python = 'python3'
    else
        let g:pymode_python = 'disable'
    endif
endif

if g:pymode_python == 'python'

    command! -nargs=1 PymodePython python <args>
    let g:UltiSnipsUsePythonVersion = 2

elseif g:pymode_python == 'python3'

    command! -nargs=1 PymodePython python3 <args>
    let g:UltiSnipsUsePythonVersion = 3

else

    let g:pymode_doc = 0
    let g:pymode_lint = 0
    let g:pymode_path = 0
    let g:pymode_rope = 0
    let g:pymode_run = 0
    let g:pymode_virtualenv = 0

    command! -nargs=1 PymodePython echo <args>

endif


command! PymodeVersion echomsg "Pymode version: " . g:pymode_version . " interpreter: " . g:pymode_python . " lint: " . g:pymode_lint . " rope: " . g:pymode_rope

augroup pymode

