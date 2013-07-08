Changelog
=========

* Added `g:pymode_rope_autocomplete_map` option;
* Removed `g:pymode_rope_map_space` option;
* Added PEP257 checker;
* Support 'pudb' in breakpoints;

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
