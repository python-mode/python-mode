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


Debian packages
---------------

Repository URL: http://klen.github.io/python-mode/deb/
Install with commands:

::

     add-apt-repository http://klen.github.io/python-mode/deb main
     apt-get update
     apt-get install vim-python-mode

If you are getting the message: "The following signatures couldn' be verified because the public key is not available": ::

    apt-key adv --keyserver keyserver.ubuntu.com --recv-keys B5DF65307000E266

`vim-python-mode` using `vim-addons`, so after installation just enable
`python-mode` with command: ::

    vim-addons install python-mode


Troubleshooting
===============

If your python-mode doesn't work:

1. Load Vim with only python-mode enabled (use `debug.vim` from pymode): ::

    vim -u <path_to_pymode>/debug.vim

And try to repeat your case. If no error occurs, seems like problem isnt in the
plugin.

2. Type `:PymodeTroubleshooting`

And fix any warnings or copy the output and send it to me. (For example, by
creating a `new github issue <https://github.com/klen/python-mode/issues/new>`_
if one does not already exist for the problem).


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
