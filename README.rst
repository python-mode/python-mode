|logo| Python-mode, Python in VIM
#################################

.. image:: https://travis-ci.org/klen/python-mode.png?branch=develop
    :target: https://travis-ci.org/klen/python-mode

.. image:: https://dl.dropboxusercontent.com/u/487440/reformal/donate.png
    :target: https://www.gittip.com/klen/
    :alt: Donate

Python-mode is a vim plugin that helps you to create python code very quickly
by utilizing libraries including pylint_, rope_, pydoc_, pyflakes_, pep8_, and
mccabe_  for features like static analysis, refactoring, folding, completion,
documentation, and more.

The plugin contains all you need to develop python applications in Vim.

There is no need to install pylint_, rope_ or any other Python libraries on
your system.

- Support Python version 2.6+ and 3.2+
- Syntax highlighting
- Virtualenv support
- Run python code (``<leader>r``)
- Add/remove breakpoints (``<leader>b``)
- Improved Python indentation
- Python folding
- Python motions and operators (``]]``, ``3[[``, ``]]M``, ``vaC``, ``viM``,
  ``daC``, ``ciM``, ...)
- Code checking  (pylint_, pyflakes_, pylama_, ...) that can be run
  simultaneously (``:PymodeLint``)
- Autofix PEP8 errors (``:PymodeLintAuto``)
- Search in python documentation (``K``)
- Code refactoring <rope refactoring library> (rope_)
- Strong code completion (rope_)
- Go to definition (``<C-c>g`` for `:RopeGotoDefinition`)
- And more, more ...

See (very old) screencast here: http://www.youtube.com/watch?v=67OZNp9Z0CQ
(sorry for quality, this is my first screencast) Another old presentation here:
http://www.youtube.com/watch?v=YhqsjUUHj6g

**To read python-mode documentation in Vim, see** ``:help pymode.txt``


.. contents::


Requirements
============

- VIM >= 7.3 (mostly features needed `+python` or `+python3` support)
  (also ``--with-features=big`` if you want ``g:pymode_lint_signs``)


How to install
==============

Using pathogen (recommended)
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


Debian packages
---------------

Repository URL: http://klen.github.io/python-mode/deb/
Install with commands:

::

     add-apt-repository http://klen.github.io/python-mode/deb main
     apt-get update
     apt-get install vim-python-mode

If you are getting the message: "The following signatures couldn't be verified because the public key is not available": ::

    apt-key adv --keyserver keyserver.ubuntu.com --recv-keys B5DF65307000E266

`vim-python-mode` using `vim-addons`, so after installation just enable
`python-mode` with command: ::

    vim-addons install python-mode


Troubleshooting
===============

If your python-mode doesn't work:

1. Load Vim with only python-mode enabled (use `debug.vim` from pymode): ::

    vim -u <path_to_pymode>/debug.vim

And try to repeat your case. If no error occurs, seems like problem isn't in the
plugin.

2. Type `:PymodeTroubleshooting`

And fix any warnings or copy the output and send it to me. (For example, by
creating a `new github issue <https://github.com/klen/python-mode/issues/new>`_
if one does not already exist for the problem).


Customization
=============

You can override the default key bindings by redefining them in your `.vimrc`, for example: ::

    " Override go-to.definition key shortcut to Ctrl-]
    let g:pymode_rope_goto_definition_bind = "<C-]>"

    " Override run current python file key shortcut to Ctrl-Shift-e
    let g:pymode_run_bind = "<C-S-e>"

    " Override view python doc key shortcut to Ctrl-Shift-d
    let g:pymode_doc_bind = "<C-S-d>"


Documentation
=============

Documentation is available in your vim ``:help pymode``


Bugtracker
===========

If you have any suggestions, bug reports or
annoyances please report them to the issue tracker
at https://github.com/klen/python-mode/issues


Contributing
============

See the `AUTHORS` file.

Development of python-mode happens at github:
https://github.com/klen/python-mode

Please make a pull request to `development` branch and add yourself to
`AUTHORS`.


Copyright
=========

Copyright © 2013 Kirill Klenov (klen_)

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
.. _rope: https://pypi.python.org/pypi/rope
.. _pylama: https://github.com/klen/pylama
.. _pylint: https://bitbucket.org/logilab/pylint
.. _pyflakes: https://pypi.python.org/pypi/pyflakes
.. _autopep8: https://github.com/hhatto/autopep8
.. _pep257: http://github.com/GreenSteam/pep257
.. _mccabe: https://github.com/flintwork/mccabe
.. _pythonvim: http://www.hlabs.spb.ru/vim/python.vim
.. _pep8: http://github.com/jcrocholl/pep8
.. _pep8indent: http://github.com/hynek/vim-python-pep8-indent
.. |logo| image:: https://raw.github.com/klen/python-mode/develop/logo.png
