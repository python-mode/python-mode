Python-mode, Python in VIM
##########################

Python-mode is a vim plugin that allows you to use the pylint_, rope_, pydoc_ library in vim to provide
features like python code looking for bugs, refactoring and some other usefull things.

This plugin allow you create python code in vim very easily.
There is no need to install the pylint_ or rope_ library on your system.

- Highlight syntax errors
- Highlight and auto fix unused imports
- Strong code completion
- Code refactoring
- Python documentation
- Run python code
- Go to definition
- Powerfull customization
- And more...

See screencast here: http://t.co/3b0bzeXA (sory for quality, this my first screencasting)


Requirements
============

- VIM >= 7.0 with python support


Installation
============

- Just copy the plugin folders into your `~/.vim` directory.

.. note:: Alternatively, if you are using pathogen_, clone the plugin into your ``bundle`` folder.

.. note:: Also you can see `:help PythonMode`

Settings
========

.. note:: Also you can see vim help. :help PythonModeOptions

To change this settings, edit your `~/.vimrc` file. Example: ::

    " Disable pylint checking every save
    let g:pymode_lint = 0

    " Set key 'R' for run python code
    let g:pymode_run_key = 'R'

Show documentation
------------------

Default values: ::

    " Load show documentation plugin
    let g:pymode_doc = 1

    " Key for show python documentation
    let g:pymode_doc_key = 'K'

    " Exetable command for documentation search
    let g:pydoc = 'pydoc'

Run python code
---------------

Default values: ::

    " Load run code plugin
    let g:pymode_run = 1

    " Key for run python code
    let g:pymode_run_key = '<leader>r'

Pylint checking
---------------

Default values: ::

    " Load pylint code plugin
    let g:pymode_lint = 1

    " Check code every save
    let g:pymode_lint_write = 1

    " Auto open cwindow if errors be finded
    let g:pymode_lint_cwindow = 1

    " Place error signs
    let g:pymode_lint_signs = 1

.. note:: 
    Pylint options (ex. disable messages) may be defined in '$HOME/pylint.rc'
    See pylint documentation.

Rope refactoring library
------------------------

Default values: ::

    " Load rope plugin
    let g:pymode_rope = 1

    " RopeVim settings
    let g:ropevim_codeassist_maxfixes=10
    let g:ropevim_guess_project=1
    let g:ropevim_vim_completion=1
    let g:ropevim_enable_autoimport=1
    let g:ropevim_autoimport_modules = ["os", "shutil"]

Other stuff
-----------

Default values: ::

    " Load breakpoints plugin
    let g:pymode_breakpoint = 1

    " Key for set/unset breakpoint
    let g:pymode_breakpoint_key = '<leader>b'

    " Load utils plugin
    let g:pymode_utils = 1

    " Autoremove unused whitespaces
    let g:pymode_utils_whitespaces = 1

.. note:: See also :help ropevim.txt


Default keys
============

.. note:: Also you can see vim help. :help PythonModeKeys

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

.. note:: See also :help ropevim.txt


Commands
========

.. note:: Also you can see vim help. :help PythonModeCommands

============== =============
Command        Description
============== =============
:Pydoc <args>  Show python documentation
-------------- -------------
PyLintToggle   Enable, disable pylint
-------------- -------------
PyLint         Check current buffer
-------------- -------------
Pyrun          Check current buffer
============== =============

.. note:: See also :help ropevim.txt


Bug tracker
===========

If you have any suggestions, bug reports or
annoyances please report them to the issue tracker
at https://github.com/klen/python-mode/issues


Contributing
============

Development of pylint-mode happens at github: https://github.com/klen/python-mode


Contributors
=============

* klen_ (Kirill Klenov)


Changelog
=========

## 2011-10-12 0.1.3
-------------------
* Fix pylint and update docs

## 2011-10-11 0.1.2
-------------------
* First public release


License
=======

Licensed under a `GNU lesser general public license`_.


.. _GNU lesser general public license: http://www.gnu.org/copyleft/lesser.html
.. _klen: http://klen.github.com/
.. _pylint: http://www.logilab.org/857
.. _rope: http://rope.sourceforge.net/
.. _pydoc: http://docs.python.org/library/pydoc.html
.. _pathogen: https://github.com/tpope/vim-pathogen
.. _plugin-helpers: https://github.com/klen/plugin-helpers
