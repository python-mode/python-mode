|logo| Python-mode, Python in VIM
#################################

.. image:: https://travis-ci.org/klen/python-mode.png?branch=develop
    :target: https://travis-ci.org/klen/python-mode

Python-mode is a vim plugin that helps you to
create python code very quickly by utilizing libraries including 
pylint_, rope_, pydoc_, pyflakes_, pep8_, and mccabe_  
for features like static analysis, refactoring, folding,
completion, documentation, and more.

There is no need to install pylint_, rope_
or any other Python libraries on your system.

- `Python motions and operators`_ (``]]``, ``3[[``, ``]]M``, ``vaC``, ``viM``, ``daC``, ``ciM``, ...)
- `Python code folding`_
- `Virtualenv support`_
- `Syntax highlighting`_
- Highlight and auto fix unused imports
- Many static analysis linters (pylint_, pyflakes_, pylama_, ...) that can be run simultaneously
- `Code refactoring <rope refactoring library>`_ (rope_)
- Strong code completion (rope_)
- Go to definition (``<C-c>g`` for `:RopeGotoDefinition`)
- `Show documentation`_ (``K``)
- Run python code (``<leader>r``)
- Powerful customization settings_
- And more, more ...


See (very old) screencast here: http://www.youtube.com/watch?v=67OZNp9Z0CQ (sorry for quality, this is my first screencast)
Another old presentation here: http://www.youtube.com/watch?v=YhqsjUUHj6g

**To read python-mode documentation in Vim, see** ``:help pymode.txt``


.. contents::


Requirements
============

- VIM >= 7.0 with python support
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

    :call pymode#troubleshooting#Test()

And fix any warnings or copy the output and send it to me.
(For example, by creating a `new github issue <https://github.com/klen/python-mode/issues/new>`_ if one does not already exist for the problem).


Settings
========

.. note:: See also ``:help PythonModeOptions``

To change these settings, edit your ``~/.vimrc``: ::

    " Disable pylint checking every save
    let g:pymode_lint_write = 0

    " Set key 'R' for run python code
    let g:pymode_run_key = 'R'


Loading the Plugin
------------------

Default values: ::

    " Load the whole plugin
    let g:pymode = 1


Show documentation
------------------

Default values: ::

    " Load show documentation plugin
    let g:pymode_doc = 1

    " Show python documentation
    let g:pymode_doc_key = 'K'


Run python code
---------------

Default values: ::

    " Load run code plugin
    let g:pymode_run = 1

    " Run python code
    let g:pymode_run_key = '<leader>r'


Code checking
-------------

Default values: ::

    " Load pylint code plugin
    let g:pymode_lint = 1

    " Switch pylint, pyflakes, pep8, mccabe code-checkers
    " Can have multiple values "pep8,pyflakes,mcccabe"
    " Choices are: pyflakes, pep8, mccabe, pylint, pep257
    let g:pymode_lint_checker = "pyflakes,pep8,mccabe"

    " Skip errors and warnings
    " E.g. "E501,W002", "E2,W" (Skip all Warnings and Errors startswith E2) and etc
    let g:pymode_lint_ignore = "E501"

    " Select errors and warnings
    " E.g. "E4,W"
    let g:pymode_lint_select = ""

    " Run linter on the fly
    let g:pymode_lint_onfly = 0

    " Pylint configuration file
    " If file not found use 'pylintrc' from python-mode plugin directory
    let g:pymode_lint_config = "$HOME/.pylintrc"

    " Check code every save
    let g:pymode_lint_write = 1

    " Auto open cwindow if errors were found
    let g:pymode_lint_cwindow = 1

    " Show error message if cursor placed at the error line
    let g:pymode_lint_message = 1

    " Auto jump on first error
    let g:pymode_lint_jump = 0

    " Hold cursor in current window
    " when quickfix is open
    let g:pymode_lint_hold = 0

    " Place error signs
    let g:pymode_lint_signs = 1

    " Maximum allowed mccabe complexity
    let g:pymode_lint_mccabe_complexity = 8

    " Minimal height of pylint error window
    let g:pymode_lint_minheight = 3

    " Maximal height of pylint error window
    let g:pymode_lint_maxheight = 6

    " Symbol definition
    let g:pymode_lint_todo_symbol = 'WW'
    let g:pymode_lint_comment_symbol = 'CC'
    let g:pymode_lint_visual_symbol = 'RR'
    let g:pymode_lint_error_symbol = 'EE'
    let g:pymode_lint_info_symbol = 'II'
    let g:pymode_lint_pyflakes_symbol = 'FF'

.. note::
    Pylint options (ex. disable messages) may be defined in ``$HOME/pylint.rc``
    See the pylint documentation: http://pylint-messages.wikidot.com/all-codes


Rope refactoring library
------------------------

Default values: ::

    " Load rope plugin
    let g:pymode_rope = 1

    " Map keys for autocompletion
    let g:pymode_rope_autocomplete_map = '<C-Space>'

    " Auto create and open ropeproject
    let g:pymode_rope_auto_project = 1

    " Enable autoimport
    let g:pymode_rope_enable_autoimport = 1

    " Auto generate global cache
    let g:pymode_rope_autoimport_generate = 1

    let g:pymode_rope_autoimport_underlineds = 0

    let g:pymode_rope_codeassist_maxfixes = 10

    let g:pymode_rope_sorted_completions = 1

    let g:pymode_rope_extended_complete = 1

    let g:pymode_rope_autoimport_modules = ["os","shutil","datetime"]

    let g:pymode_rope_confirm_saving = 1

    let g:pymode_rope_global_prefix = "<C-x>p"

    let g:pymode_rope_local_prefix = "<C-c>r"

    let g:pymode_rope_vim_completion = 1

    let g:pymode_rope_guess_project = 1

    let g:pymode_rope_goto_def_newwin = ""

    let g:pymode_rope_always_show_complete_menu = 0


Python code folding
-------------------

Default values: ::

    " Enable python code folding
    let g:pymode_folding = 1


Python motions and operators
--------------------------------

Default values: ::

    " Enable python objects and motion
    let g:pymode_motion = 1


Virtualenv support
------------------

Default values: ::

    " Auto fix vim python paths if virtualenv enabled
    let g:pymode_virtualenv = 1


Other stuff
-----------

Default values: ::

    " Additional python paths
    let g:pymode_paths = []

    " Load breakpoints plugin
    let g:pymode_breakpoint = 1

    " Key for set/unset breakpoint
    let g:pymode_breakpoint_key = '<leader>b'

    " Autoremove unused whitespaces
    let g:pymode_utils_whitespaces = 1

    " Enable pymode indentation
    let g:pymode_indent = 1

    " Set default pymode python options
    let g:pymode_options = 1


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
    let g:pymode_syntax_slow_sync = 0


Default keys
============

.. note:: See also ``:help PythonModeKeys``

============== =============
Keys           Command
============== =============
**K**          Show python docs (``g:pymode_doc enabled``)
-------------- -------------
**<C-Space>**  Rope autocomplete (``g:pymode_rope enabled``)
-------------- -------------
**<C-c>g**     Rope goto definition  (``g:pymode_rope enabled``)
-------------- -------------
**<C-c>d**     Rope show documentation  (``g:pymode_rope enabled``)
-------------- -------------
**<C-c>f**     Rope find occurrences  (``g:pymode_rope enabled``)
-------------- -------------
**<Leader>r**  Run python  (``g:pymode_run enabled``)
-------------- -------------
**<Leader>b**  Set, unset breakpoint (``g:pymode_breakpoint enabled``)
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

.. note:: See also ``:help ropevim.txt``


Commands
========

.. note:: See also ``:help PythonModeCommands``

==================== =============
Command              Description
==================== =============
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

.. note:: See also ``:help ropevim.txt``


F.A.Q.
======

Rope completion is very slow
----------------------------

rope_ creates a project-level service directory in ``.ropeproject``.

If ``g:pymode_rope_guess_project`` is set (as it is by default),
and ``.ropeproject`` is not found in the current directory,
rope will walk upwards looking for a ``.ropeproject`` in every dir of the parent path.

If rope finds ``.ropeproject`` in a parent dir,
it sets the project for all child dirs
and the scan may be slow for so many dirs and files.

Solutions:

- Disable ``g:pymode_rope_guess_project`` to make rope always create ``.ropeproject`` in the current dir.
- Delete ``.ropeproject`` from the parent dir to make rope create ``.ropeproject`` in the current dir.
- Press ``<C-x>po`` or ``:RopeOpenProject`` to make rope create ``.ropeproject`` in the current dir.



Pylint check is very slow
-------------------------

In some projects, pylint_ may check slowly because it also scans imported modules if posible.
Alternately, use pyflakes_. 

.. note:: See also ``:help 'pymode_lint_checker'``.

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
.. |logo| image:: https://raw.github.com/klen/python-mode/develop/logo.png
