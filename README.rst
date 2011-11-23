Python-mode, Python in VIM
##########################

Python-mode is a vim plugin that allows you to use the pylint_, rope_, pydoc_, pyflakes_ libraries in vim to provide
features like python code looking for bugs, refactoring and some other useful things.

This plugin allow you create python code in vim very easily.
There is no need to install the pylint_, rope_ or any used python library on your system.

- Highlight syntax errors
- Highlight and auto fix unused imports
- Strong code completion
- Code refactoring
- Python documentation
- Run python code
- Go to definition
- Powerful customization
- Virtualenv support
- And more...

See screencast here: http://t.co/3b0bzeXA (sorry for quality, this is my first screencast)


.. contents::


Requirements
============

- VIM >= 7.0 with python support
  (also ``--with-features=big`` if you want use g:pymode_lint_signs)



How to install
==============


Using pathogen_ (recomended)
----------------------------
::

    % cd ~/.vim
    % mkdir -p bundle && cd bundle
    % git clone git://github.com/klen/python-mode.git

- Enable pathogen_ in your ``~/.vimrc``: ::

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
    % cd python-mode.vim
    % cp -R * ~/.vim

Then rebuild **helptags** in vim::

    :helptags ~/.vim/doc/


.. note:: **filetype-plugin** (``:help filetype-plugin-on``) and **filetype-indent** (``:help filetype-indent-on``)
    must be enabled for use python-mode.


Settings
========

.. note:: Also you can see vim help. ``:help PythonModeOptions``

To change this settings, edit your ``~/.vimrc``: ::

    " Disable pylint checking every save
    let g:pymode_lint_write = 0

    " Set key 'R' for run python code
    let g:pymode_run_key = 'R'


Show documentation
------------------

Default values: ::

    " Load show documentation plugin
    let g:pymode_doc = 1

    " Key for show python documentation
    let g:pymode_doc_key = 'K'

    " Executable command for documentation search
    let g:pydoc = 'pydoc'


Run python code
---------------

Default values: ::

    " Load run code plugin
    let g:pymode_run = 1

    " Key for run python code
    let g:pymode_run_key = '<leader>r'


Code checking
-------------

Default values: ::

    " Load pylint code plugin
    let g:pymode_lint = 1

    " Switch pylint or pyflakes code checker
    " values (pylint, pyflakes)
    let g:pymode_lint_checker = "pylint"

    " Pylint configuration file
    " If file not found use 'pylintrc' from python-mode plugin directory
    let g:pymode_lint_config = "$HOME/.pylintrc"

    " Check code every save
    let g:pymode_lint_write = 1

    " Auto open cwindow if errors be finded
    let g:pymode_lint_cwindow = 1

    " Auto jump on first error
    let g:pymode_lint_jump = 0

    " Place error signs
    let g:pymode_lint_signs = 1

    " Minimal height of pylint error window
    let g:pymode_lint_minheight = 3

    " Maximal height of pylint error window
    let g:pymode_lint_maxheight = 6


.. note:: 
    Pylint options (ex. disable messages) may be defined in ``$HOME/pylint.rc``
    See pylint documentation: http://pylint-messages.wikidot.com/all-codes


Rope refactoring library
------------------------

Default values: ::

    " Load rope plugin
    let g:pymode_rope = 1

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

    let g:pymode_rope_autoimport_modules = ["os","shutil","datetime"])

    let g:pymode_rope_confirm_saving = 1

    let g:pymode_rope_global_prefix = "<C-x>p"

    let g:pymode_rope_local_prefix = "<C-c>r"

    let g:pymode_rope_vim_completion = 1

    let g:pymode_rope_guess_project = 1

    let g:pymode_rope_goto_def_newwin = 0

    let g:pymode_rope_always_show_complete_menu = 0


Other stuff
-----------

Default values: ::

    " Load breakpoints plugin
    let g:pymode_breakpoint = 1

    " Key for set/unset breakpoint
    let g:pymode_breakpoint_key = '<leader>b'

    " Autoremove unused whitespaces
    let g:pymode_utils_whitespaces = 1

    " Auto fix vim python paths if virtualenv enabled
    let g:pymode_virtualenv = 1

    " Set default pymode python indent options
    let g:pymode_options_indent = 1

    " Set default pymode python fold options
    let g:pymode_options_fold = 1

    " Set default pymode python other options
    let g:pymode_options_other = 1


Syntax highlight
----------------

Default values: ::

    " Enable pymode's custom syntax highlighting
    let g:pymode_syntax = 1

    " Enable all python highlightings
    let g:pymode_syntax_all = 1

    " Highlight "print" as function
    leg g:pymode_syntax_print_as_function = 0

    " Highlight indentation errors
    leg g:pymode_syntax_indent_errors = g:pymode_syntax_all

    " Highlight trailing spaces
    leg g:pymode_syntax_space_errors = g:pymode_syntax_all

    " Highlight string formatting
    leg g:pymode_syntax_string_formatting = g:pymode_syntax_all

    " Highlight str.format syntax
    leg g:pymode_syntax_string_format = g:pymode_syntax_all

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

    " For fast machines
    let g:pymode_syntax_slow_sync = 0


Default keys
============

.. note:: Also you can see vim help ``:help PythonModeKeys``

============== =============
Keys           Command
============== =============
**K**          Show python docs
-------------- -------------
**<C-Space>**  Rope autocomplete
-------------- -------------
**<Leader>r**  Run python
-------------- -------------
**<Leader>b**  Set, unset breakpoint
============== =============

.. note:: See also ``:help ropevim.txt``


Commands
========

.. note:: Also you can see vim help ``:help PythonModeCommands``

==================== =============
Command              Description
==================== =============
:Pydoc <args>        Show python documentation
-------------------- -------------
PyLintToggle         Enable, disable pylint
-------------------- -------------
PyLintCheckerToggle  Toggle code checker (pylint, pyflakes)
-------------------- -------------
PyLint               Check current buffer
-------------------- -------------
Pyrun                Run current buffer in python
==================== =============

.. note:: See also ``:help ropevim.txt``


F.A.Q.
======

Rope completion is very slow
----------------------------

To work rope_ creates a service directory: ``.ropeproject``.
If ``g:pymode_rope_guess_project`` set (by default) and ``.ropeproject`` in current dir not found, rope scan ``.ropeproject`` on every dir in parent path.
If rope finded ``.ropeproject`` in parent dirs, rope set project for all child dir and scan may be slow for many dirs and files.

Solutions:

- Disable ``g:pymode_rope_guess_project`` to make rope always create ``.ropeproject`` in current dir.
- Delete ``.ropeproject`` from dip parent dir to make rope create ``.ropeproject`` in current dir.
- Press ``<C-x>po`` or ``:RopeOpenProject`` to make force rope create ``.ropeproject`` in current dir.



Pylint check is very slow
-------------------------

In some projects pylint_ may check slowly, because it also scan imported modules if posible.
Try use pyflakes_, see ``:h 'pymode_lint_checker'``.

.. note:: You may ``set exrc`` and ``set secure`` in your ``vimrc`` for auto set custom settings from ``.vimrc`` from your projects directories.
    Example: On Flask projects I automaticly set ``g:pymode_lint_checker = "pyflakes"``, on django ``g:pymode_lint_cheker = "pylint"``



Bugtracker
===========

If you have any suggestions, bug reports or
annoyances please report them to the issue tracker
at https://github.com/klen/python-mode/issues


Contributing
============

Development of pylint-mode happens at github: https://github.com/klen/python-mode


Copyright
=========

Copyright (C) 2011 Kirill Klenov (klen_)

    **Rope**
        Copyright (C) 2006-2010 Ali Gholami Rudi

        Copyright (C) 2009-2010 Anton Gritsay

    **Pylint**
        Copyright (C) 2003-2011 LOGILAB S.A. (Paris, FRANCE).
        http://www.logilab.fr/

    **Pyflakes**:
        Copyright (c) 2005 Divmod, Inc.
        http://www.divmod.com/

    **Python syntax for vim**
        Copyright (c) 2010 Dmitry Vasiliev
        http://www.hlabs.spb.ru/vim/python.vim


License
=======

Licensed under a `GNU lesser general public license`_.


.. _GNU lesser general public license: http://www.gnu.org/copyleft/lesser.html
.. _klen: http://klen.github.com/
.. _pylint: http://www.logilab.org/857
.. _pyflakes: http://pypi.python.org/pypi/pyflakes
.. _rope: http://rope.sourceforge.net/
.. _pydoc: http://docs.python.org/library/pydoc.html
.. _pathogen: https://github.com/tpope/vim-pathogen
