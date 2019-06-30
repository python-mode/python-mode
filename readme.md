[![Build Status](https://travis-ci.org/python-mode/python-mode.svg?branch=develop)](https://travis-ci.org/python-mode/python-mode)

![](https://raw.github.com/python-mode/python-mode/develop/logo.png)
# Python-mode, a Python IDE for Vim

-------------------------------------------------------------------------------

*This project needs contributors.*

**Documentation:**
- ``:help pymode``
- <https://github.com/python-mode/python-mode/wiki>

-------------------------------------------------------------------------------

<p align="center">
  <img width="150" height="150" src="https://vignette.wikia.nocookie.net/sqmegapolis/images/4/42/Warning-2-256.png/revision/latest?cb=20130403220740">
</p>

***Important***: From 2017-11-19 onwards python-mode uses submodules instead of
hard coding 3rd party libraries into its codebase. Please issue the command:
`git submodule update --init --recursive`
inside your python-mode folder.

If you are a new user please clone the repos using the recursive flag:
`git clone --recurse-submodules https://github.com/python-mode/python-mode`

-------------------------------------------------------------------------------

Python-mode is a Vim plugin that magically converts Vim into a Python IDE.

Why Python-mode?

1.  **Be more productive**: Pymode saves time by bringing all the tools
    necessary for professional developers so that you can focus on bigger
    things. It has been finely tuned based on decades of experience working
    with Vim and is constantly kept up to date.
2.  **Get smart assistance**: Pymode knows all about your code. We use the
    best-in-class intellisense code completion, on-the-fly error checking and
    quick-fixes; easy project navigation and much more.
3.  **Use the full power and capabilities of Vim**: Unlike traditional IDEs
    which can only provide a small subset of Vim functionalities, you can do
    everything and anything that you can in Vim.
4.  **Modular structure**: We attempt to create Python-mode with the same
    principles of python: i.e. have a modular structure, so that as and when
    better libraries evolve, we can provide you the best experience, while
    abstracting the details so that you can get back to what you do best.
5.  **Written mostly in Python**: 96.1% written in Python. Well, we love Python
    :)

The plugin contains all you need to develop python applications in Vim.

* Support Python version 2.6+ and 3.2+
* Syntax highlighting
* Virtualenv support
* Run python code (`<leader>r`)
* Add/remove breakpoints (`<leader>b`)
* Improved Python indentation
* Python motions and operators (`]]`, `3[[`, `]]M`, `vaC`, `viM`,
  `daC`, `ciM`, ...)
* Improved Python folding
* Run multiple code checkers simultaneously (`:PymodeLint`)
* Autofix PEP8 errors (`:PymodeLintAuto`)
* Search in python documentation (`<leader>K`)
* Code refactoring
* Intellisense code-completion
* Go to definition (`<C-c>g`)
* And more, more ...

See a screencast here: <http://www.youtube.com/watch?v=67OZNp9Z0CQ>.

Another old presentation here: <http://www.youtube.com/watch?v=YhqsjUUHj6g>.

**To read python-mode documentation in Vim, use** `:help pymode`.

# Requirements

Vim >= 7.3 (most features needed +python or +python3 support) (also
`--with-features=big` if you want `g:pymode_lint_signs`).

# How to install

## Manually (according to vim's package structure)

As of vim8 there is an officially supported way of adding plugins. See `:tab
help packages` in vim for details.

    cd ~/.vim/pack/python-mode/start
    git clone --recurse-submodules https://github.com/python-mode/python-mode.git
    cd python-mode

Note. Windows OS users need to add `-c core.symlinks=true`. See below.

## pathogen

    cd ~/.vim
    mkdir -p bundle && cd bundle
    git clone --recurse-submodules https://github.com/python-mode/python-mode.git


Enable [pathogen](https://github.com/tpope/vim-pathogen) in your `~/.vimrc`:

    " Pathogen load
    filetype off

    call pathogen#infect()
    call pathogen#helptags()

    filetype plugin indent on
    syntax on

## vim-plug

Include the following in the [vim-plug](https://github.com/junegunn/vim-plug)
section of your `~/.vimrc`:

    Plug 'python-mode/python-mode', { 'for': 'python', 'branch': 'develop' }

## NeoBundle

Add the following:

    " python-mode: PyLint, Rope, Pydoc, breakpoints from box.
    " https://github.com/python-mode/python-mode
    NeoBundleLazy 'python-mode/python-mode', { 'on_ft': 'python' }

## Manually

    % git clone --recurse-submodules https://github.com/python-mode/python-mode.git
    % cd python-mode
    % cp -R * ~/.vim

Then rebuild **helptags** in vim:

    :helptags ~/.vim/doc/

**filetype-plugin** (`:help filetype-plugin-on`) and **filetype-indent**
(`:help filetype-indent-on`) must be enabled to use python-mode.

# Troubleshooting/Debugging

First read our short
[FAQ](https://github.com/python-mode/python-mode/blob/develop/doc/pymode.txt)
or using `:help pymode-faq`.
If your question is not described there then you already know what to do
(because you read the first item of our FAQ :) ).

Nevertheless just a refresher on how to submit bugs:

**(From the FAQ)**

Clear all python cache/compiled files (`*.pyc` files and `__pycache__`
directory and everything under it). In Linux/Unix/MacOS you can run:

`find . -type f -name '*.pyc' -delete && find . -type d -name '__pycache__' -delete`

Then start python mode with:

`vim -i NONE -u <path_to_pymode>/debugvimrc.vim`

Reproduce the error and submit your python mode debug file. You can check its
location with `:messages` for something like:

> pymode debug msg 1: Starting debug on: 2017-11-18 16:44:13 with file /tmp/pymode_debug_file.txt

Please submit the entire content of the file along with a reasoning of why the
plugin seems broken.

***Do check for sensitive information in the file before submitting.***

Please, also provide more contextual information such as:

* your Operational System (Linux, WIndows, Mac) and which version
* the `vim --version` output
* which is your default python (`python --version`)
* the python version that vim has loaded in your tests:
    * `:PymodePython import sys; print(sys.version_info)` output.
* and if you are using virtualenvs and/or conda, also state that, please.

# Frequent problems

Read this section before opening an issue on the tracker.

## Python 3 syntax

By default python-mode uses python 2 syntax checking. To enable python 3 syntax
checking (e.g. for async) add:

    let g:pymode_python = 'python3'

To your vimrc or exrc file.

## Symlinks on Windows

Users on Windows OS might need to add `-c core.symlinks=true` switch to
correctly clone / pull repository. Example: `git clone --recurse-submodules
https://github.com/python-mode/python-mode -c core.symlinks=true`

## Error updating the plugin

If you are trying to update the plugin (using a plugin manager or manually) and
you are seeing an error such as:

> Server does not allow request for unadvertised object

Then we probably changed some repo reference or some of our dependencies had a
`git push --force` in its git history. So the best way for you to handle it is
to run, inside the `python-mode` directory:

`git submodule update --recursive --init --force`
`git submodule sync --recursive`

# Documentation

Documentation is available in your vim `:help pymode`.

# Bugtracker

If you have any suggestions, bug reports or annoyances please report them to
the issue tracker at:
<https://github.com/python-mode/python-mode/issues>

# Contributing

The contributing guidelines for this plugin are outlined at
`:help pymode-development`.

* Author: Kirill Klenov (<https://github.com/klen>)
* Maintainers:
    * Felipe Vieira (<https://github.com/fmv1992>)
    * Diego Rabatone Oliveira (<https://github.com/diraol>)

Also see the AUTHORS file.

Development of python-mode happens at github:
<https://github.com/python-mode/python-mode>

Please make a pull request to development branch and add yourself to AUTHORS.

### Python libraries

Vendored Python modules are located mostly in
[pymode/libs/](https://github.com/python-mode/python-mode/tree/develop/pymode/libs).

# Copyright

Copyright © 2013-2015 Kirill Klenov (<https://github.com/klen>).

# License

Licensed under a [GNU lesser general public license]().

If you like this plugin, I would very appreciated if you kindly send me
a postcard :) My address is here: "Russia, 143500, MO, Istra, pos. Severny 8-3"
to "Kirill Klenov". **Thanks for support!**
