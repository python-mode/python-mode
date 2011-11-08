Python-mode, Python in VIM
##########################

Python-mode is a vim plugin that allows you to use the pylint_, rope_, pydoc_ library in vim to provide
features like python code looking for bugs, refactoring and some other useful things.

This plugin allow you create python code in vim very easily.
There is no need to install the pylint_ or rope_ library on your system.

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

See screencast here: http://t.co/3b0bzeXA (sorry for quality, this my first screencast)


Requirements
============

- VIM >= 7.0 with python support
  (also `--with-features=big` if you want use g:pymode_lint_signs)



How to install
==============


Using pathogen_ (recomended)
----------------------------
::

    % cd ~/.vim
    % mkdir -p bundle && cd bundle
    % git clone git://github.com/klen/python-mode.git

- Enable pathogen_ in your `~/.vimrc`: ::

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

Then rebuild helptags in vim::

    :helptags ~/.vim/doc/


.. note:: filetype-plugin (`:help filetype-plugin-on`) and filetype-indent (`:help filetype-indent-on`)
    must be enabled for use python-mode.


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
    let g:pymode_lint_checker = "pylint"

    " Pylint configuration file
    " If file not found use '.pylintrc' from python-mode plugin directory
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
    Pylint options (ex. disable messages) may be defined in '$HOME/pylint.rc'
    See pylint documentation.


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
PyLintCheckerToggle  Toggle code checker (pylint, pyflakes)
-------------- -------------
PyLint         Check current buffer
-------------- -------------
Pyrun          Run current buffer in python
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


Copyright
=========

Copyright (C) 2011 Kirill Klenov (klen_)

    **Rope**
        Copyright (C) 2006-2010 Ali Gholami Rudi

        Copyright (C) 2009-2010 Anton Gritsay

    **Pylint**
        Copyright (C) 2003-2011 LOGILAB S.A. (Paris, FRANCE).
        http://www.logilab.fr/


License
=======

Licensed under a `GNU lesser general public license`_.


.. _GNU lesser general public license: http://www.gnu.org/copyleft/lesser.html
.. _klen: http://klen.github.com/
.. _pylint: http://www.logilab.org/857
.. _rope: http://rope.sourceforge.net/
.. _pydoc: http://docs.python.org/library/pydoc.html
.. _pathogen: https://github.com/tpope/vim-pathogen
