|logo| Python-mode, Python in VIM
#################################

.. image:: https://travis-ci.org/klen/python-mode.png?branch=develop
    :target: https://travis-ci.org/klen/python-mode

Python-mode is a vim plugin that helps you to create python code very quickly
by utilizing libraries including pylint_, rope_, pydoc_, pyflakes_, pep8_, and
mccabe_  for features like static analysis, refactoring, folding, completion,
documentation, and more.

The plugin containts all you need to develop python applications in Vim.

There is no need to install pylint_, rope_ or any other Python libraries on
your system.

- Support Python version 2.6+ and 3.2+
- Syntax highlighting
- Virtualenv support
- Run python code (``<leader>r``)
- Add/remove breakpoints (``<leader>b``)
- Improved Python indentation
- Python folding
- Python motions and operators (``]]``, ``3[[``, ``]]M``, ``vaC``, ``viM``, ``daC``, ``ciM``, ...)
- Code checking  (pylint_, pyflakes_, pylama_, ...) that can be run simultaneously (``:PymodeLint``)
- Autofix PEP8 errors (``:PymodeLintAuto``)
- Search in python documentation (``K``)
- Code refactoring <rope refactoring library> (rope_)
- Strong code completion (rope_)
- Go to definition (``<C-c>g`` for `:RopeGotoDefinition`)
- And more, more ...

See (very old) screencast here: http://www.youtube.com/watch?v=67OZNp9Z0CQ (sorry for quality, this is my first screencast)
Another old presentation here: http://www.youtube.com/watch?v=YhqsjUUHj6g

**To read python-mode documentation in Vim, see** ``:help pymode.txt``


.. contents::


Requirements
============

- VIM >= 7.3 (mostly features needed `+python` or `+python3` support)
  (also ``--with-features=big`` if you want ``g:pymode_lint_signs``)


How to install
==============

Using pathogen (recomended)
----------------------------
::

    % cd ~/.vim
    % mkdir -p bundle && cd bundle
    % git clone git://github.com/klen/python-mode.git

- Enable `pathogen <https://github.com/tpope/vim-pathogen>`_
  in your ``~/.vimrc``: ::

    " Pathogen load
    filetype off

    call pathogen#infect()
    call pathogen#helptags()

    filetype plugin indent on
    syntax on


Manually
--------
::

    % git clone git://github.com/klen/python-mode.git
    % cd python-mode
    % cp -R * ~/.vim

Then rebuild **helptags** in vim::

    :helptags ~/.vim/doc/


.. note:: **filetype-plugin**  (``:help filetype-plugin-on``) and
   **filetype-indent** (``:help filetype-indent-on``)
   must be enabled to use python-mode.


Troubleshooting
===============

If your python-mode doesn't work: open any python file and type: ::

    :call pymode#troubleshooting#test()

And fix any warnings or copy the output and send it to me. (For example, by
creating a `new github issue <https://github.com/klen/python-mode/issues/new>`_
if one does not already exist for the problem).


Settings
========

.. note:: See also ``:help PythonModeOptions``

.. note:: To change these settings, edit your ``~/.vimrc``

Bellow shows the default settings.

Basic settings
--------------

Enable/disable the Plugin
^^^^^^^^^^^^^^^^^^^^^^^^^

Default values: ::

    " Enable pymode (plugin will be loaded)
    let g:pymode = 1


Python version
^^^^^^^^^^^^^^

Choose prefer version of Vim python interpreter::

    let g:pymode_python = 'python'

Anycase **pymode** try to define python interpreter automaticaly.

Values are `python`, `python3`, `disable`. If value set to `disable` most
python-features of **pymode** will be disabled.


Enable/disable warnings
^^^^^^^^^^^^^^^^^^^^^^^

Show pymode warnings.

Default value: ::

    let g:pymode_warning = 1


Append path to sys.path
^^^^^^^^^^^^^^^^^^^^^^^

Value is list of path's strings. 

Default value: ::

    let g:pymode_paths = []


Enable pymode python indent
^^^^^^^^^^^^^^^^^^^^^^^^^^^

PEP8 compatible python indent.

Default value: ::

    let g:pymode_indent = 1


Enable pymode python folding
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Fast and usual python folding in Vim.

Default value: ::

    let g:pymode_folding = 1


Enable Vim motion for python objects
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Support Vim motion `:Help operator` for python objects (such as functions,
class, methods).

'C' — means class
'M' — means method or function

Examples:

`viC` - visual select Class content.
`daM` - delete current method, function
`]C`, `]]`  - goto next class/function definition

Default value: ::

    let g:pymode_motion = 1


Trim unused whitespaces on save
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Default value: ::

    let g:pymode_trim_whitespaces = 1


Setup default python options
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Default value: ::

    let g:pymode_options = 1

Setup pymode quickfix window
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Set size for quickfix window wich opened pymode (errors, occurencies).

::

    let g:pymode_quickfix_minheight = 3
    let g:pymode_quickfix_maxheight = 6


Show documentation (pydoc)
--------------------------

Default values: ::

    " Load show documentation functionality
    let g:pymode_doc = 1

    " Bind keys to show documentation for current word (selection)
    let g:pymode_doc_bind = 'K'


Support virtualenv
------------------

Enable virtualenv detection::

    let g:pymode_virtualenv = 1

Set path to virtualenv by manually::

    let g:pymode_virtualenv_path = $VIRTUAL_ENV


Run python code in current buffer (selection)
---------------------------------------------

Default values: ::

    " Enable code run functionality
    let g:pymode_run = 1

    " Binds keys to run current buffer (selection)
    let g:pymode_run_bind = '<leader>r'


Set/unset breakpoints
---------------------

Pymode automatically detect available debugger (like pdb, ipdb, pudb) and user
could set/unset breakpoint with one key and without code checking and etc.

Enable functionality::

    let g:pymode_breakpoint = 1

Bind keys to set/unset breakpoints::

    let g:pymode_breakpoint_bind = '<leader>b'

Manually set breakpoint command (leave empty for automatic detection)::

    let g:pymode_breakpoint_cmd = ''


Code checking (pylint, pep8, pep257, pyflakes, mccabe)
------------------------------------------------------

.. note:: Pymode uses Pylama_ library for code checking. Many options like skip
    files, errors and etc could be defined in `pylama.ini` file or modelines.
    Check Pylama_ documentation for details.

.. note::
    Pylint options (ex. disable messages) may be defined in ``$HOME/pylint.rc``
    See the pylint documentation: http://pylint-messages.wikidot.com/all-codes

Enable code checking functionality: ::

    let g:pymode_lint = 1

Check code on every save: ::

    let g:pymode_lint_on_write = 1

Check code on every insert: ::

    let g:pymode_lint_on_fly = 1

Show error message if cursor placed at the error line: ::

    let g:pymode_lint_message = 1

Default code checkers (you could set several): ::

    let g:pymode_lint_checkers = ['pyflakes', 'pep8', 'mccabe']

Values may be choosen: `pylint`, `pep8`, `mccabe`, `pep257`, `pyflakes`.

Skip errors and warnings:
E.g. "E501,W002", "E2,W" (Skip all Warnings and Errors startswith E2) and etc: ::

    let g:pymode_lint_ignore = "E501,W"

Force select some error or warnings. (by example you disable all warnings
starting from 'W', but want see warning 'W0011' and warning 'W430')::

    let g:pymode_lint_select = "E501,W0011,W430"

Auto open cwindow (quickfix) if any errors has been finded: ::

    let g:pymode_lint_cwindow = 1

Place error signs: ::

    let g:pymode_lint_signs = 1

Symbol definitions: ::

    let g:pymode_lint_todo_symbol = 'WW'
    let g:pymode_lint_comment_symbol = 'CC'
    let g:pymode_lint_visual_symbol = 'RR'
    let g:pymode_lint_error_symbol = 'EE'
    let g:pymode_lint_info_symbol = 'II'
    let g:pymode_lint_pyflakes_symbol = 'FF'


Rope refactoring, code inspection, autocomplete
-----------------------------------------------

Pymode have Rope_ support (python2, python3).

Enable rope functionality: ::

    let g:pymode_rope = 1

Enable code completion with Rope_: ::

    let g:pymode_rope_completion = 1

Open completion menu when user type dot: ::

    let g:pymode_rope_complete_on_dot = 1

Bind keys for completion (<C-x><C-o> will be binded too): ::

    let g:pymode_rope_completion_bind = '<C-Space>'

Bind keys to go to definition object under cursor: ::

    let g:pymode_rope_goto_definition_bind = '<C-c>g'

Command for open window when definition has been finded ('e', 'new', 'vnew'): ::

    let g:pymode_rope_goto_definition_cmd = 'new'

Bind keys for show documentation for object under cursor (leave empty for disable): ::

    let g:pymode_rope_show_doc_bind = '<C-c>d'

Bind keys for find occurencies for object under cursor (leave empty for disable): ::

    let g:pymode_rope_find_it_bind = '<C-c>f'

Bind keys for organize imports in current buffer (leave empty for disable): ::

    let g:pymode_rope_orgazine_imports_bind = '<C-c>ro'

Bind keys for rename variable/method/class under cursor in the whole project
(leave empty for disable): ::

    let g:pymode_rope_rename_bind = '<C-c>rr'

Bind keys for rename a current module: ::

    let g:pymode_rope_rename_module_bind = '<C-c>r1r'

Bind keys for convert module to package: ::

    let g:pymode_rope_module_to_package_bind = '<C-c>r1p'

Creates a new function or method (depending on the context) from the selected lines: ::

    let g:pymode_rope_extract_method_bind = '<C-c>rm'

Creates a variable from the selected lines: ::

    let g:pymode_rope_extract_variable_bind = '<C-c>rl'

Bind Inline refactoring: ::

    let g:pymode_rope_inline_bind = '<C-c>ri'

Bind Move refactoring: ::

    let g:pymode_rope_move_bind = '<C-c>rv'


Syntax highlighting
-------------------

Default values: ::

    " Enable pymode's custom syntax highlighting
    let g:pymode_syntax = 1

    " Enable all python highlightings
    let g:pymode_syntax_all = 1

    " Highlight "print" as a function
    let g:pymode_syntax_print_as_function = 0

    " Highlight indentation errors
    let g:pymode_syntax_indent_errors = g:pymode_syntax_all

    " Highlight trailing spaces
    let g:pymode_syntax_space_errors = g:pymode_syntax_all

    " Highlight string formatting
    let g:pymode_syntax_string_formatting = g:pymode_syntax_all

    " Highlight str.format syntax
    let g:pymode_syntax_string_format = g:pymode_syntax_all

    " Highlight string.Template syntax
    let g:pymode_syntax_string_templates = g:pymode_syntax_all

    " Highlight doc-tests
    let g:pymode_syntax_doctests = g:pymode_syntax_all

    " Highlight builtin objects (__doc__, self, etc)
    let g:pymode_syntax_builtin_objs = g:pymode_syntax_all

    " Highlight builtin functions
    let g:pymode_syntax_builtin_funcs = g:pymode_syntax_all

    " Highlight exceptions
    let g:pymode_syntax_highlight_exceptions = g:pymode_syntax_all

    " Highlight equal operator
    let g:pymode_syntax_highlight_equal_operator = g:pymode_syntax_all

    " Highlight stars operator
    let g:pymode_syntax_highlight_stars_operator = g:pymode_syntax_all

    " Highlight `self`
    let g:pymode_syntax_highlight_self = g:pymode_syntax_all

    " For fast machines
    let g:pymode_syntax_slow_sync = 1


Default keys
============

.. note:: See also ``:help PythonModeKeys``

============== =============
Keys           Command
============== =============
**K**          Show python docs
-------------- -------------
**<C-Space>**  Pymode autocomplete
-------------- -------------
**<C-c>g**     Rope goto definition
-------------- -------------
**<C-c>d**     Rope show documentation
-------------- -------------
**<C-c>f**     Rope find occurrences
-------------- -------------
**<C-c>ro**    Rope organize imports in current buffer
-------------- -------------
**<C-c>rr**    Rename object under cursor in whole project
-------------- -------------
**<C-c>rm**    Create new function or method from selected lines (extract)
-------------- -------------
**<C-c>r1r**   Rename current module
-------------- -------------
**<C-c>r1p**   Convert current module to package
-------------- -------------
**<Leader>r**  Run code
-------------- -------------
**<Leader>b**  Set, unset breakpoint
-------------- -------------
``[[``         Jump to previous class or function (normal, visual, operator modes)
-------------- -------------
``]]``         Jump to next class or function  (normal, visual, operator modes)
-------------- -------------
``[M``         Jump to previous class or method (normal, visual, operator modes)
-------------- -------------
``]M``         Jump to next class or method (normal, visual, operator modes)
-------------- -------------
``aC``, ``C``  Select a class. Ex: ``vaC``, ``daC``, ``dC``, ``yaC``, ``yC``, ``caC``, ``cC`` (normal, operator modes)
-------------- -------------
``iC``             Select inner class. Ex: ``viC``, ``diC``, ``yiC``, ``ciC`` (normal, operator modes)
-------------- -------------
``aM``, ``M``  Select a function or method. Ex: ``vaM``, ``daM``, ``dM``, ``yaM``, ``yM``, ``caM``, ``cM`` (normal, operator modes)
-------------- -------------
``iM``         Select inner function or method. Ex: ``viM``, ``diM``, ``yiM``, ``ciM`` (normal, operator modes)
============== =============


Commands
========

.. note:: See also ``:help PythonModeCommands``

==================== =============
Command              Description
==================== =============
:PymodeVersion       Show version of installed pymode
-------------------- -------------
:PymodePython <args> Run python code in current pymode interpreter
-------------------- -------------
:PymodeRun           Run current buffer or selected lines
-------------------- -------------
:PymodeLint          Run code checking in current buffer
-------------------- -------------
:PymodeLintAuto      Fix PEP8 errors in current buffer automaticaly
-------------------- -------------
:PymodeLintToggle    Toggle code checking
-------------------- -------------
:PymodeDoc <args>    Show python documentation
-------------------- -------------
:PymodeRopeNewProject Open new Rope project in current working directory
-------------------- -------------
:PymodeRopeUndo      Undo changes from last refactoring
-------------------- -------------
:PymodeRopeRedo      Redo changes from last refactoring
-------------------- -------------
:PymodeRopeRenameModule Rename current module
-------------------- -------------
:PymodeRopeModuleToPackage Convert current module to package
-------------------- -------------
:PymodeRopeRegenerate Regenerate the project cache
-------------------- -------------
:PymodeRopeAutoImport Autoimport used modules
-------------------- -------------

:Pydoc <args>        Show python documentation
-------------------- -------------
:PyLintToggle        Enable/disable pylint
-------------------- -------------
:PyLintCheckerToggle Toggle code checker (pylint, pyflakes)
-------------------- -------------
:PyLint              Check current buffer
-------------------- -------------
:PyLintAuto          Automatically fix PEP8 errors
-------------------- -------------
:Pyrun               Run current buffer in python
==================== =============


F.A.Q.
======

Rope completion is very slow
----------------------------

Rope_ creates a project-level service directory in ``.ropeproject``.

If ``.ropeproject`` is not found in the current directory,
rope will walk upwards looking for a ``.ropeproject`` in every dir of the parent path.

If rope finds ``.ropeproject`` in a parent dir,
it sets the project for all child dirs
and the scan may be slow for so many dirs and files.

Solutions:

- Delete ``.ropeproject`` from the parent dir to make rope create ``.ropeproject`` in the current dir.
- Run ``:PymodeRopeNewProject`` to make rope create ``.ropeproject`` in the current dir.


Pylint check is very slow
-------------------------

In some projects, pylint_ may check slowly because it also scans imported modules if posible.
Alternately, use pyflakes_. 

.. note:: See also ``:help 'pymode_lint_checkers'``.

.. note:: You may ``set exrc`` and ``set secure`` in your ``vimrc`` to auto set custom settings from a ``.vimrc`` in your projects' directories.
    Example: On Flask projects I automatically set ``g:pymode_lint_checker = "pyflakes"``, on django ``g:pymode_lint_cheker = "pylint"``


OSX cannot import urandom
-------------------------

See: https://groups.google.com/forum/?fromgroups=#!topic/vim_dev/2NXKF6kDONo

The sequence of commands that fixed this: ::

    brew unlink python
    brew unlink macvim
    brew remove macvim
    brew install -v --force macvim
    brew link macvim
    brew link python


Bugtracker
===========

If you have any suggestions, bug reports or
annoyances please report them to the issue tracker
at https://github.com/klen/python-mode/issues


Contributing
============

See the `AUTHORS` file.

Development of python-mode happens at github: https://github.com/klen/python-mode


Copyright
=========

Copyright © 2013 Kirill Klenov (klen_)

Rope
-----
Copyright (C) 2006-2010 Ali Gholami Rudi

Copyright (C) 2009-2010 Anton Gritsay

https://pypi.python.org/pypi/rope

https://pypi.python.org/pypi/ropemode

http://rope.sourceforge.net/ropevim.html


Pylama
------
Copyright (C) 2012-2013 Kirill Klenov

https://pypi.python.org/pypi/pylama

https://github.com/klen/pylama


Pylint
------
Copyright (C) 2003-2011 LOGILAB S.A. (Paris, FRANCE).

https://pypi.python.org/pypi/pylint

https://bitbucket.org/logilab/pylint

http://www.pylint.org/

http://www.logilab.fr/


Pyflakes
--------

Copyright (c) 2005 Divmod, Inc.

https://pypi.python.org/pypi/pyflakes

https://launchpad.net/pyflakes

http://www.divmod.com/


pep8
----
Copyright (C) 2006 Johann C. Rocholl <johann@rocholl.net>

https://pypi.python.org/pypi/pep8

http://github.com/jcrocholl/pep8

http://www.python.org/dev/peps/pep-0008/


autopep8
--------
Copyright (C) 2010-2011 Hideo Hattori <hhatto.jp@gmail.com

Copyright (C) 2011-2013 Hideo Hattori, Steven Myint

https://pypi.python.org/pypi/autopep8

https://github.com/hhatto/autopep8


pep257
-------
Copyright (C) 2012 Vladimir Keleshev, GreenSteam A/S

https://pypi.python.org/pypi/pep257

http://github.com/GreenSteam/pep257

http://www.python.org/dev/peps/pep-0257/


mccabe
------
Copyright (C) 2008 Ned Batchelder

Copyright (C) 2013 Florent Xicluna

https://pypi.python.org/pypi/mccabe

https://github.com/flintwork/mccabe


Python syntax for vim
----------------------
Copyright (c) 2010 Dmitry Vasiliev

http://www.hlabs.spb.ru/vim/python.vim


PEP8 VIM indentation
---------------------
Copyright (c) 2012 Hynek Schlawack <hs@ox.cx>

http://github.com/hynek/vim-python-pep8-indent


License
=======

Licensed under a `GNU lesser general public license`_.

If you like this plugin, you can send me postcard :)
My address is here: "Russia, 143401, Krasnogorsk, Shkolnaya 1-19" to "Kirill Klenov".
**Thanks for support!**


.. _GNU lesser general public license: http://www.gnu.org/copyleft/lesser.html
.. _klen: http://klen.github.com/
.. _pydoc: http://docs.python.org/library/pydoc.html
.. _pathogen: https://github.com/tpope/vim-pathogen
.. _mccabe: http://en.wikipedia.org/wiki/Cyclomatic_complexity
.. _Rope: http://rope.sourceforge.net/
.. _Pylama: https://github.com/klen/pylama
.. |logo| image:: https://raw.github.com/klen/python-mode/develop/logo.png
