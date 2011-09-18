Python-mode, Python in VIM
==========================

Python-mode is a vim plugin that allows you to use the pylint_, rope_, pydoc_ library in vim to provide
features like python code looking for bugs, refactoring and some other usefull things.

This plugin allow you create python code in vim very easily.
There is no need to install the pylint_ or rope_ library on your system.


Requirements
------------

- VIM >= 7.0 with python support
- plugin-helpers_ -- vim plugin


Installation
------------

- First plugin-helpers_ must be installed.
- Just copy the plugin folders into your `~/.vim` directory.

.. note:: Alternatively, if you are using pathogen_, clone the plugin into your ``bundle`` folder.


Settings
--------

To change this settings, edit your `~/.vimrc` file. Default values: ::

    " Python interpreter
    let g:python = 'python'

    " Pydoc command
    let g:pydoc = 'pydoc'

    " Trim trailing whitespace
    let g:pymode_whitespaces = 1

    " Pylint disable messages
    let g:pymode_lint_disable = "C0103,C0111,C0301,W0141,W0142,W0212,W0221,W0223,W0232,W0401,W0613,W0631,E1101,E1120,R0903,R0904,R0913"

    " Pylint show quickfix window
    let g:pymode_lint_cwindow = 1

    " Pylint place signs
    let g:pymode_lint_signs = 1

    " Pylint check on write
    let g:pymode_lint_write = 1

.. note:: See also :help ropevim.txt


Keys
----

K -- Show python docs
<C-Space> -- Rope autocomplete
<Leader>r -- Run python
<Leader>b -- Set, unset breakpoint

.. note:: See also :help ropevim.txt


Commands
--------
Pydoc <args> -- Show python documentation
PyLintToggle -- Enable, disable pylint for current buffer
PyLint -- Check current buffer

.. note:: See also :help ropevim.txt


Bug tracker
-----------

If you have any suggestions, bug reports or
annoyances please report them to the issue tracker
at https://github.com/klen/python-mode/issues


Contributing
------------

Development of pylint-mode happens at github: https://github.com/klen/python-mode


Contributors
-------------

* klen_ (Kirill Klenov)


License
-------

Licensed under a `GNU lesser general public license`_.


.. _GNU lesser general public license: http://www.gnu.org/copyleft/lesser.html
.. _klen: http://klen.github.com/
.. _pylint: http://www.logilab.org/857
.. _rope: http://rope.sourceforge.net/
.. _pydoc: http://docs.python.org/library/pydoc.html
.. _pathogen: https://github.com/tpope/vim-pathogen
.. _plugin-helpers: https://github.com/klen/plugin-helpers
