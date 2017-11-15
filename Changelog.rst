Changelog
=========


## TODO
-------
* Move changelog rst syntax to markdown
* pymode_rope: check disables
* When loading a file without a history, substituting a word (eg 'cw') moves
  the cursor to position 0 (equivalent to 'cw' then '0l')
    * Fixed on `917e484`
* Inspect why files starting with:
~~~~~~
def main():
    pass


if __name__ == '__main__':
    main()
~~~~~~
do not get loaded.


## 2017-07-xxx 0.9.5
--------------------
* pylama: migrated to submodule


## 2017-07-11 0.9.4
--------------------
* pylama: fixed erratic behavior of `skip` option causing unintended skipping
  of lint checkers
* PEP257 requires `snowbalstemmer`: added as submodule
* Fixed handling of `g:pymode_lint_ignore` and `g:pymode_lint_select`: from
  strings to list
* Migrated modules from `pymode/libs` to `submodules/ <https://github.com/fmv1992/python-mode/tree/develop/submodules>`__
    * Rationale: no need to single handedly update each module; removes burden
      from developers
* Improved folding accuracy
    * Improved nested definitions folding
    * Improved block delimiting


## (changelog poorly maintained) 0.8.2
--------------------------------------
* Pylama updated to version 5.0.5
* Rope libs updated
* Add wdb to debugger list in breakpoint cmd
* Add 'pymode_options_max_line_length' option
* Add ability to set related checker options `:help pymode-lint-options`
  Options added: 'pymode_lint_options_pep8', 'pymode_lint_options_pep257',
  'pymode_lint_options_mccabe', 'pymode_lint_options_pyflakes',
  'pymode_lint_options_pylint'
* Highlight comments inside class/function arg lists
* Don't fold single line def
* Don't skip a line when the first docstring contains text
* Add Python documentation vertical display option
* Rope: correct refactoring function calls


## 2014-06-11 0.8.1
-------------------
* Pylama updated to version 3.3.2
* Get fold's expression symbol from &fillchars;
* Fixed error when setting g:pymode_breakpoint_cmd (expobrain);
* Fixed code running;
* Ability to override rope project root and .ropeproject folder
* Added path argument to `PymodeRopeNewProject` which skips prompt
* Disable `pymode_rope_lookup_project` by default
* Options added:
    'pymode_rope_project_root', 'pymode_rope_ropefolder'


## 2013-12-04 0.7.8b
--------------------
    * Update indentation support;
    * Python3 support;
    * Removed pymode modeline support;
    * Disabled async code checking support;
    * Options changes:
        'pymode_doc_key' -> 'pymode_doc_bind'
        'pymode_run_key' -> 'pymode_run_bind'
        'pymode_breakpoint_key' -> 'pymode_breakpoint_bind'
        'pymode_breakpoint_template' -> 'pymode_breakpoint_cmd'
        'pymode_lint_write' -> 'pymode_lint_on_write'
        'pymode_lint_onfly' -> 'pymode_lint_on_fly'
        'pymode_lint_checker' -> 'pymode_lint_checkers'
        'pymode_lint_minheight' -> 'pymode_quickfix_minheight'
        'pymode_lint_maxheight' -> 'pymode_quickfix_maxheight'
        'pymode_rope_autocomplete_map' -> 'pymode_rope_completion_bind'
        'pymode_rope_enable_autoimport' -> 'pymode_rope_autoimport'

    * Options removed:

        'pymode_lint_hold', 'pymode_lint_config', 'pymode_lint_jump',
        'pymode_lint_signs_always_visible', 'pymode_rope_extended_complete',
        'pymode_rope_auto_project', 'pymode_rope_autoimport_generate',
        'pymode_rope_autoimport_underlines', 'pymode_rope_codeassist_maxfixes',
        'pymode_rope_sorted_completions', 'pymode_rope_extended_complete',
        'pymode_rope_confirm_saving', 'pymode_rope_global_prefix',
        'pymode_rope_local_prefix', 'pymode_rope_vim_completion',
        'pymode_rope_guess_project', 'pymode_rope_goto_def_newwin',
        'pymode_rope_always_show_complete_menu'

    * Options added:
        'pymode_rope_regenerate_on_write', 'pymode_rope_completion',
        'pymode_rope_complete_on_dot', 'pymode_lint_sort',
        'pymode_rope_lookup_project', 'pymode_lint_unmodified'

    * Commands added:
        'PymodeVirtualenv'

    * Commands changed:
        'PyDoc' -> 'PymodeDoc'
        'Pyrun' -> 'PymodeRun'
        'PyLintToggle' -> 'PymodeLintToggle'
        'PyLint' -> 'PymodeLint'
        'PyLintAuto' -> 'PymodeLintAuto'
        'RopeOpenProject' -> 'PymodeRopeNewProject'
        'RopeUndo' -> 'PymodeRopeUndo'
        'RopeRedo' -> 'PymodeRopeRedo'
        'RopeRenameCurrentModule' -> 'PymodeRopeRenameModule'
        'RopeModuleToPackage' -> 'PymodeRopeModuleToPackage'
        'RopeGenerateAutoimportCache' -> 'PymodeRopeRegenerate'
        'RopeOrgamizeImports' -> 'PymodeRopeAutoImport'

    * Commands removed:
        'PyLintCheckerToggle', 'RopeCloseProject', 'RopeProjectConfig',
        'RopeRename', 'RopeCreate<...>', 'RopeWriteProject', 'RopeRename',
        'RopeExtractVariable', 'RopeExtractMethod', 'RopeInline', 'RopeMove',
        'RopeRestructure', 'RopeUseFunction', 'RopeIntroduceFactory',
        'RopeChangeSignature', 'RopeMoveCurrentModule',
        'RopeGenerate<...>', 'RopeAnalizeModule', 'RopeAutoImport',


## 2013-10-29 0.6.19
--------------------
* Added `g:pymode_rope_autocomplete_map` option;
* Removed `g:pymode_rope_map_space` option;
* Added PEP257 checker;
* Support 'pudb' in breakpoints;
* Pyrun can now operate on a range of lines, and does not need to save (c) lawrenceakka
* Update pylama to version 1.5.0
* Add a set of `g:pymode_lint_*_symbol` options (c) kdeldycke;
* Support virtualenv for python3 (c) mlmoses;

## 2013-05-15 0.6.18
--------------------
* Fixed autopep8 (`PyLintAuto`) command;
* Fix error on non-ascii characters in docstrings;
* Update python syntax;

## 2013-05-03 0.6.17
--------------------
* Update `Pylint` to version 0.28.0;
* Update `pyflakes` to version 0.7.3;
* Fixed `lint_ignore` options bug;
* Fixed encoding problems when code running;

## 2013-04-26 0.6.16
--------------------
* Improvement folding (thanks @alvinfrancis);

## 2013-04-01 0.6.15
--------------------
* Bugfix release

## 2013-03-16 0.6.14
--------------------
* Update `PEP8` to version 1.4.5;
* Update `Pylint` to version 0.27.0;
* Update `pyflakes` to version 0.6.1;
* Update `autopep8` to version 0.8.7;
* Fix breakpoint definition;
* Update python syntax;
* Fixed run-time error when output non-ascii in multibyte locale;
* Move initialization into ftplugin as it is python specific;
* Pyrex (Cython) files support;
* Support `raw_input` in run python code;

## 2012-09-07 0.6.10
--------------------
* Dont raise an exception when Logger has no message handler (c) nixon
* Improve performance of white space removal (c) Dave Smith
* Improve ropemode support (c) s0undt3ch
* Add `g:pymode_updatetime` option
* Update autopep8 to version 0.8.1

## 2012-09-07 0.6.9
-------------------
* Update autopep8
* Improve pymode#troubleshooting#Test()

## 2012-09-06 0.6.8
-------------------
* Add PEP8 indentation ":help 'pymode_indent'"

## 2012-08-15 0.6.7
-------------------
* Fix documentation. Thanks (c) bgrant;
* Fix pymode "async queue" support.

## 2012-08-02 0.6.6
-------------------
* Updated Pep8 to version 1.3.3
* Updated Pylint to version 0.25.2
* Fixed virtualenv support for windows users
* Added pymode modeline ':help PythonModeModeline'
* Added diagnostic tool ':call pymode#troubleshooting#Test()'
* Added `PyLintAuto` command ':help PyLintAuto'
* Code checking is async operation now
* More, more fast the pymode folding
* Repaired execution of python code

## 2012-05-24 0.6.4
-------------------
* Add 'pymode_paths' option
* Rope updated to version 0.9.4

## 2012-04-18 0.6.3
-------------------
* Fix pydocs integration

## 2012-04-10 0.6.2
-------------------
* Fix pymode_run for "unnamed" clipboard
* Add 'pymode_lint_mccabe_complexity' option
* Update Pep8 to version 1.0.1
* Warning! Change 'pymode_rope_goto_def_newwin' option
  for open "goto definition" in new window, set it to 'new' or 'vnew'
  for horizontally or vertically split
  If you use default behaviour (in the same buffer), not changes needed.

## 2012-03-13 0.6.0
-------------------
* Add 'pymode_lint_hold' option
* Improve pymode loading speed
* Add pep8, mccabe lint checkers
* Now g:pymode_lint_checker can have many values
  Ex. "pep8,pyflakes,mccabe"
* Add 'pymode_lint_ignore' and 'pymode_lint_select' options
* Fix rope keys
* Fix python motion in visual mode
* Add folding 'pymode_folding'
* Warning: 'pymode_lint_checker' now set to 'pyflakes,pep8,mccabe' by default

## 2012-02-12 0.5.8
-------------------
* Fix pylint for Windows users
* Python documentation search running from Vim (delete g:pydoc option)
* Python code execution running from Vim (delete g:python option)

## 2012-02-11 0.5.7
-------------------
* Fix 'g:pymode_lint_message' mode error
* Fix breakpoints
* Fix python paths and virtualenv detection

## 2012-02-06 0.5.6
-------------------
* Fix 'g:pymode_syntax' option
* Show error message in bottom part of screen
  see 'g:pymode_lint_message'
* Fix pylint for windows users
* Fix breakpoint command (Use pdb when idpb not installed)

## 2012-01-17 0.5.5
-------------------
* Add a sign for info messages from pylint.
  (c) Fredrik Henrysson
* Change motion keys: vic - viC, dam - daM and etc
* Add 'g:pymode_lint_onfly' option

## 2012-01-09 0.5.3
-------------------
* Prevent the configuration from breaking python-mode
  (c) Dirk Wallenstein

## 2012-01-08 0.5.2
-------------------
* Fix ropeomnicompletion
* Add preview documentation

## 2012-01-06 0.5.1
-------------------
* Happy new year!
* Objects and motion  fixes

## 2011-11-30 0.5.0
-------------------
* Add python objects and motions (beta)
  :h pymode_motion

## 2011-11-27 0.4.8
-------------------
* Add `PyLintWindowToggle` command
* Fix some bugs

## 2011-11-23 0.4.6
-------------------
* Enable all syntax highlighting
  For old settings set in your vimrc:

  ::

    let g:pymode_syntax_builtin_objs = 0
    let g:pymode_syntax_builtin_funcs = 0

* Change namespace of syntax variables
  See README

## 2011-11-18 0.4.5
-------------------
* Add 'g:pymode_syntax' option
* Highlight 'self' keyword

## 2011-11-16 0.4.4
-------------------
* Minor fixes

## 2011-11-11 0.4.3
-------------------
* Fix pyflakes

## 2011-11-09 0.4.2
-------------------
* Add FAQ
* Some refactoring and fixes

## 2011-11-08 0.4.0
-------------------
* Add alternative code checker "pyflakes"
  See :h 'pymode_lint_checker'
* Update install docs

## 2011-10-30 0.3.3
-------------------
* Fix RopeShowDoc

## 2011-10-28 0.3.2
-------------------
* Add 'g:pymode_options_*' stuff, for ability
  to disable default pymode options for python buffers

## 2011-10-27 0.3.1
-------------------
* Add 'g:pymode_rope_always_show_complete_menu' option
* Some pylint fixes

## 2011-10-25 0.3.0
-------------------
* Add g:pymode_lint_minheight and g:pymode_lint_maxheight
  options
* Fix PyLintToggle
* Fix Rope and PyLint libs loading

## 2011-10-21 0.2.12
--------------------
* Auto open cwindow with results
  on rope find operations

## 2011-10-20 0.2.11
--------------------
* Add 'pymode_lint_jump' option

## 2011-10-19 0.2.10
--------------------
* Minor fixes (virtualenv loading, buffer commands)

## 2011-10-18 0.2.6
-------------------
* Add <C-space> shortcut for macvim users.
* Add VIRTUALENV support

## 2011-10-17 0.2.4
-------------------
* Add current work path to sys.path
* Add 'g:pymode' option (disable/enable pylint and rope)
* Fix pylint copyright
* Hotfix rope autocomplete

## 2011-10-15 0.2.1
-------------------
* Change rope variables (ropevim_<name> -> pymode_rope_<name>)
* Add "pymode_rope_auto_project" option (default: 1)
* Update and fix docs
* 'pymode_rope_extended_complete' set by default
* Auto generate rope project and cache
* "<C-c>r a" for RopeAutoImport

## 2011-10-12 0.1.4
-------------------
* Add default pylint configuration

## 2011-10-12 0.1.3
-------------------
* Fix pylint and update docs

## 2011-10-11 0.1.2
-------------------
* First public release
