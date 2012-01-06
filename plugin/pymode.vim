let g:pymode_version = "0.5.1"

com! PymodeVersion echomsg "Current python-mode version: " . g:pymode_version

" OPTION: g:pymode -- bool. Run pymode.
if pymode#Default('g:pymode', 1) || !g:pymode
    " DESC: Disable script loading
    finish
endif

" DESC: Check python support
if !has('python')
    echoerr expand("<sfile>:t") . " required vim compiled with +python."
    echoerr "Pymode rope, pylint and virtualenv plugins will be disabled."
    let g:pymode_lint = 0
    let g:pymode_rope = 0
    let g:pymode_path = 0
    let g:pymode_virtualenv = 0
endif

" DESC: Fix python path
if !pymode#Default('g:pymode_path', 1) || g:pymode_path
python << EOF
import sys, vim
from os import path as op

sys.path = [
    op.join(op.dirname(op.dirname(vim.eval("expand('<sfile>:p')"))),
    'pylibs'), vim.eval("getcwd()") ] + sys.path
EOF
endif


" Lint {{{

if !pymode#Default("g:pymode_lint", 1) || g:pymode_lint

    " OPTION: g:pymode_lint_write -- bool. Check code every save.
    call pymode#Default("g:pymode_lint_write", 1)

    " OPTION: g:pymode_lint_checker -- str. Use pylint of pyflakes for check.
    call pymode#Default("g:pymode_lint_checker", "pylint")

    " OPTION: g:pymode_lint_config -- str. Path to pylint config file
    call pymode#Default("g:pymode_lint_config", $HOME . "/.pylintrc")

    " OPTION: g:pymode_lint_cwindow -- bool. Auto open cwindow if errors find
    call pymode#Default("g:pymode_lint_cwindow", 1)

    " OPTION: g:pymode_lint_jump -- int. Jump on first error.
    call pymode#Default("g:pymode_lint_jump", 0)

    " OPTION: g:pymode_lint_minheight -- int. Minimal height of pymode lint window
    call pymode#Default("g:pymode_lint_minheight", 3)

    " OPTION: g:pymode_lint_maxheight -- int. Maximal height of pymode lint window
    call pymode#Default("g:pymode_lint_maxheight", 6)

    " OPTION: g:pymode_lint_signs -- bool. Place error signs
    if !pymode#Default("g:pymode_lint_signs", 1) || g:pymode_lint_signs

        " DESC: Signs definition
        sign define W text=WW texthl=Todo
        sign define C text=CC texthl=Comment
        sign define R text=RR texthl=Visual
        sign define E text=EE texthl=Error

    endif

    " DESC: Set default pylint configuration
    if !filereadable(g:pymode_lint_config)
        let g:pymode_lint_config = expand("<sfile>:p:h:h") . "/pylint.ini"
    endif

python << EOF
import os
import StringIO
import _ast
import re

from logilab.astng.builder import MANAGER
from pylint import lint, checkers
from pyflakes import checker


# Pylint setup
linter = lint.PyLinter()
pylint_re = re.compile('^[^:]+:(\d+): \[([EWRCI]+)[^\]]*\] (.*)$')

checkers.initialize(linter)
linter.set_option("output-format", "parseable")
linter.set_option("reports", 0)
linter.load_file_configuration(vim.eval("g:pymode_lint_config"))

# Pyflakes setup

# Pylint check
def pylint():
    filename = vim.current.buffer.name
    MANAGER.astng_cache.clear()
    linter.reporter.out = StringIO.StringIO()
    linter.check(filename)
    qf = []
    for w in linter.reporter.out.getvalue().split('\n'):
        test = pylint_re.match(w)
        test and qf.append(dict(
                filename = filename,
                bufnr = vim.current.buffer.number,
                lnum = test.group(1),
                type = test.group(2),
                text = test.group(3).replace("'", "\""),
            ))
    vim.command('let b:qf_list = %s' % repr(qf))

# Pyflakes check
def pyflakes():
    filename = vim.current.buffer.name
    codeString = file(filename, 'U').read() + '\n'
    qf = []
    try:
        tree = compile(codeString, filename, "exec", _ast.PyCF_ONLY_AST)

    except SyntaxError, value:
        msg = value.args[0]
        if codeString is None:
            vim.command('echoerr "%s: problem decoding source"' % filename)
        else:
            lineno, _, text = value.lineno, value.offset, value.text
            qf.append(dict(
                filename = filename,
                bufnr = vim.current.buffer.number,
                lnum = str(lineno),
                text = msg,
                type = 'E'
            ))

    else:
        w = checker.Checker(tree, filename)
        w.messages.sort(lambda a, b: cmp(a.lineno, b.lineno))
        for w in w.messages:
            qf.append(dict(
                filename = filename,
                bufnr = vim.current.buffer.number,
                lnum = str(w.lineno),
                text = w.message % w.message_args,
                type = 'E'
            ))

    vim.command('let b:qf_list = %s' % repr(qf))
EOF
endif

" }}}


" Breakpoints {{{

if !pymode#Default("g:pymode_breakpoint", 1) || g:pymode_breakpoint

    " OPTION: g:pymode_breakpoint_key -- string. Key for set/unset breakpoint.
    call pymode#Default("g:pymode_breakpoint_key", "<leader>b")

    call pymode#Default("g:pymode_breakpoint_cmd", "import ipdb; ipdb.set_trace() ### XXX BREAKPOINT")

endif

" }}}


" Documentation {{{

if !pymode#Default("g:pymode_doc", 1) || g:pymode_doc

    if !pymode#CheckProgram("pydoc", "or disable pymode_doc.")
        let g:pymode_doc = 0
    endif

    " OPTION: g:pymode_doc_key -- string. Key for show python documantation.
    call pymode#Default("g:pymode_doc_key", "K")

endif

" }}}


" Virtualenv {{{

if !pymode#Default("g:pymode_virtualenv", 1) || g:pymode_virtualenv

    call pymode#Default("g:pymode_virtualenv_enabled", [])

endif

" }}}


" Execution {{{

if !pymode#Default("g:pymode_run", 1) || g:pymode_run

    if !pymode#CheckProgram("python", "or disable pymode_run.")
        let g:pymode_run = 0
    endif

    " OPTION: g:pymode_doc_key -- string. Key for show python documantation.
    call pymode#Default("g:pymode_run_key", "<leader>r")

endif

" }}}


" Rope {{{

if !pymode#Default("g:pymode_rope", 1) || g:pymode_rope

    " OPTION: g:pymode_rope_auto_project -- bool. Auto open ropeproject
    call pymode#Default("g:pymode_rope_auto_project", 1)

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

    " OPTION: g:pymode_rope_vim_completion -- bool.
    call pymode#Default("g:pymode_rope_vim_completion", 1)

    " OPTION: g:pymode_rope_guess_project -- bool.
    call pymode#Default("g:pymode_rope_guess_project", 1)

    " OPTION: g:pymode_rope_goto_def_newwin -- bool.
    call pymode#Default("g:pymode_rope_goto_def_newwin", 0)

    " OPTION: g:pymode_rope_always_show_complete_menu -- bool.
    call pymode#Default("g:pymode_rope_always_show_complete_menu", 0)

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

endif

" }}}


" OPTION: g:pymode_utils_whitespaces -- bool. Remove unused whitespaces on save
call pymode#Default("g:pymode_utils_whitespaces", 1)

" vim: fdm=marker:fdl=0

