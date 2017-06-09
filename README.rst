|logo| Python-mode, Python in VIM
#################################

.. image:: https://travis-ci.org/python-mode/python-mode.png?branch=develop
    :target: https://travis-ci.org/python-mode/python-mode

-----

*The project needs contributors*

** Python-mode Slack Channel is here: https://python-mode.herokuapp.com/ **

-----

|
| Src:  https://github.com/python-mode/python-mode
| Homepage: https://klen.github.io/python-mode/
| Docs: https://github.com/python-mode/python-mode/blob/develop/doc/pymode.txt
|

Python-mode is a vim plugin that helps you to create python code very quickly
by utilizing libraries including
`pylint`_, `rope`_, pydoc_, `pyflakes`_, `pep8`_, `autopep8`_,
`pep257`_ and `mccabe`_
for features like static analysis, refactoring, folding, completion,
documentation, and more.

The plugin contains all you need to develop python applications in Vim.

There is no need to install `pylint`_, `rope`_
or any other `Python Libraries`_ on your system.

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

**To read python-mode documentation in Vim, see** ``:help pymode``


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
    % git clone https://github.com/python-mode/python-mode.git

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

    % git clone https://github.com/python-mode/python-mode.git
    % cd python-mode
    % cp -R * ~/.vim

Then rebuild **helptags** in vim::

    :helptags ~/.vim/doc/


.. note:: **filetype-plugin**  (``:help filetype-plugin-on``) and
   **filetype-indent** (``:help filetype-indent-on``)
   must be enabled to use python-mode.


Debian packages
---------------
|Repository URL: https://klen.github.io/python-mode/deb/

Install with commands:

::

     add-apt-repository https://klen.github.io/python-mode/deb main
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
creating a `new github issue <https://github.com/python-mode/python-mode/issues/new>`_
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


Frequent Problems
=================

Read this section before opening an issue on the tracker.

Python 3 Syntax
---------------

By default python-mode uses python 2 syntax checking. To enable python 3
syntax checking (e.g. for async) add::

    let g:pymode_python = 'python3'

To your vimrc or exrc file


Documentation
=============

Documentation is available in your vim ``:help pymode``


Bugtracker
===========

If you have any suggestions, bug reports or
annoyances please report them to the issue tracker
at https://github.com/python-mode/python-mode/issues


Contributing
============

* Kirill Klenov (horneds@gmail.com)
* Bryce Guinta (https://github.com/brycepg)

Also see the `AUTHORS` file.

Development of python-mode happens at github:
https://github.com/python-mode/python-mode

Please make a pull request to `development` branch and add yourself to
`AUTHORS`.

Source Links
===================
- `doc/pymode.txt
  <https://github.com/python-mode/python-mode/blob/develop/doc/pymode.txt>`__
  -- ``:help pymode``
- `plugin/pymode.vim
  <https://github.com/python-mode/python-mode/blob/develop/plugin/pymode.vim>`__
  -- python-mode VIM plugin
- `syntax/python.vim
  <https://github.com/python-mode/python-mode/blob/develop/syntax/python.vim>`__
  -- python-mode ``python.vim`` VIM syntax
- `syntax/pyrex.vim
  <https://github.com/python-mode/python-mode/blob/develop/syntax/pyrex.vim>`__
  -- ``pyrex.vim`` VIM syntax (pyrex, Cython)
- `t/
  <https://github.com/python-mode/python-mode/tree/develop/t>`__
  -- ``*.vim`` more python-mode VIM configuration
- `pymode/
  <https://github.com/python-mode/python-mode/tree/develop/pymode>`__
  -- ``*.py`` -- python-mode Python module
- `pymode/libs/
  <https://github.com/python-mode/python-mode/tree/develop/pymode/libs>`__
  -- ``*.py`` -- `Python Libraries <#python-libraries>`__


Python Libraries
------------------
Vendored Python modules are located
mostly in
`pymode/libs/ <https://github.com/python-mode/python-mode/tree/develop/pymode/libs>`__.


======
rope
======
| PyPI: https://pypi.python.org/pypi/rope
| Src: https://github.com/python-rope/rope
| Docs: https://github.com/python-rope/rope/blob/master/docs/overview.rst
| Docs: https://github.com/python-rope/rope/blob/master/docs/library.rst

========================
ropemode
========================
| PyPI: https://pypi.python.org/pypi/ropemode
| Src: https://github.com/python-rope/ropemode

=========
ropevim
=========
| PyPI: https://pypi.python.org/pypi/ropevim
| Src: https://github.com/python-rope/ropevim
| Docs: https://github.com/python-rope/ropevim/blob/master/doc/ropevim.txt

=======
pylama
=======
| PyPI: https://pypi.python.org/pypi/pylama
| Src: https://github.com/klen/pylama

========
pylint
========
| PyPI: https://pypi.python.org/pypi/pylint
| Src: https://bitbucket.org/logilab/pylint
| Homepage: http://www.pylint.org/
| Docs: http://docs.pylint.org/
| Docs: http://docs.pylint.org/message-control.html
| Docs: http://docs.pylint.org/faq.html#message-control
| ErrCodes: http://pylint-messages.wikidot.com/all-codes
| ErrCodes: http://pylint-messages.wikidot.com/all-messages

==========
pyflakes
==========
| PyPI: https://pypi.python.org/pypi/pyflakes
| Src: https://github.com/pyflakes/pyflakes
| ErrCodes: https://flake8.readthedocs.org/en/latest/warnings.html

======
pep8
======
| PyPI: https://pypi.python.org/pypi/pep8
| Src: http://github.com/jcrocholl/pep8
| PEP 8: http://www.python.org/dev/peps/pep-0008/
| PEP 8: http://legacy.python.org/dev/peps/pep-0008/
| Docs: https://pep8.readthedocs.org/en/latest/
| Docs: https://pep8.readthedocs.org/en/latest/intro.html#configuration
| ErrCodes: https://pep8.readthedocs.org/en/latest/intro.html#error-codes

=========
autopep8
=========
| PyPI: https://pypi.python.org/pypi/autopep8
| Src: https://github.com/hhatto/autopep8

=======
pep257
=======
| PyPI: https://pypi.python.org/pypi/pep257
| Src: http://github.com/GreenSteam/pep257
| Docs: https://pep257.readthedocs.org/en/latest/
| PEP 257: http://www.python.org/dev/peps/pep-0257/
| ErrCodes: https://pep257.readthedocs.org/en/latest/error_codes.html

=======
mccabe
=======
| PyPI: https://pypi.python.org/pypi/mccabe
| Src: https://github.com/flintwork/mccabe
| Docs: https://en.wikipedia.org/wiki/Cyclomatic_complexity


Vim Libraries
---------------
Vendored Vim modules are located mostly in ``t/``.

======================
Python syntax for vim
======================
| Src: http://www.hlabs.spb.ru/vim/python.vim


=====================
PEP8 VIM indentation
=====================
| Src: http://github.com/hynek/vim-python-pep8-indent



Copyright
=========

Copyright © 2013-2015 Kirill Klenov (klen_)

License
=======

Licensed under a `GNU lesser general public license`_.

If you like this plugin, I would very appreciated if you kindly send me a postcard :)
My address is here: "Russia, 143500, MO, Istra, pos. Severny 8-3" to "Kirill Klenov".
**Thanks for support!**

.. _GNU lesser general public license: http://www.gnu.org/copyleft/lesser.html
.. _klen: https://klen.github.com/
.. _pydoc: http://docs.python.org/library/pydoc.html
.. _pathogen: https://github.com/tpope/vim-pathogen
.. _rope_: https://pypi.python.org/pypi/rope
.. _pylama_: https://github.com/klen/pylama
.. _pylint_: https://bitbucket.org/logilab/pylint
.. _pyflakes_: https://pypi.python.org/pypi/pyflakes
.. _autopep8_: https://github.com/hhatto/autopep8
.. _pep257_: http://github.com/GreenSteam/pep257
.. _mccabe_: https://github.com/flintwork/mccabe
.. _pythonvim: http://www.hlabs.spb.ru/vim/python.vim
.. _pep8_: http://github.com/jcrocholl/pep8
.. _pep8indent: http://github.com/hynek/vim-python-pep8-indent
.. |logo| image:: https://raw.github.com/python-mode/python-mode/develop/logo.png
