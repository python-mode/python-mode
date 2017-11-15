![](https://raw.github.com/python-mode/python-mode/develop/logo.png)
# Python-mode, a Python IDE for Vim

-------------------------------------------------------------------------------

*This project needs contributors.*

**Please use python-mode tag on Stackoverflow to ask questions:**  
<https://stackoverflow.com/questions/tagged/python-mode>

-------------------------------------------------------------------------------

Python-mode is a Vim plugin that magically converts Vim into a Python IDE.

Why Python-mode?

1.  **Be more productive**: Pymode saves time by bring all tools necessary for
    professional developers so that you can focus on bigger things. It has been
    finely tuned based on decades of experience working with Vim and is
    constantly kept uptodate.
2.  **Get smart assistance**: Pymode knows all about your code. We use the
    best-in-class intellisense code completion, on-the-fly error checking and
    quick-fixes; easy project navigation and much more.
3.  **Use the full power and capabilities of Vim**: Unlike traditional IDEs
    which can only provide a small subset of Vim functionalities, you can do
    everything and anything that you can in Vim.
4.  **Modular structure**: We attempt to be create Python-mode in the same
    principles of python: i.e. have a modular structure, so that as and when
    better libraries evolve, we can provide you the best experience, while
    abstracting the details so that you can get back to what you do best.
5.  **Written mostly in Python**: 96.1% written in Python. Well we love Python
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

See a screencast here: <http://www.youtube.com/watch?v=67OZNp9Z0CQ>  
Another old presentation here: <http://www.youtube.com/watch?v=YhqsjUUHj6g>

**To read python-mode documentation in Vim, use** `:help pymode`.

# Requirements

Vim >= 7.3 (most features needed +python or +python3 support) (also
`--with-features=big` if you want `g:pymode_lint_signs`).

# How to install

## Manually (according to vim's package structure)

As of vim8 there is an officially supported way of adding plugins. See `:tab
help packages` in vim for details.

    cd ~/.vim/pack/foo/start
    git clone https://github.com/python-mode/python-mode.git
    cd python-mode
    git submodule update --init --recursive


## Using pathogen

    % cd ~/.vim
    % mkdir -p bundle && cd bundle
    % git clone https://github.com/python-mode/python-mode.git

Enable [pathogen](https://github.com/tpope/vim-pathogen) in your `~/.vimrc`:

    " Pathogen load
    filetype off

    call pathogen#infect()
    call pathogen#helptags()

    filetype plugin indent on
    syntax on

## Manually

    % git clone https://github.com/python-mode/python-mode.git
    % cd python-mode
    % cp -R * ~/.vim

Then rebuild **helptags** in vim:

    :helptags ~/.vim/doc/

**filetype-plugin** (`:help filetype-plugin-on`) and **filetype-indent**
(`:help filetype-indent-on`) must be enabled to use python-mode.

# Troubleshooting

If your python-mode doesn't work:

1. Load Vim with only python-mode enabled (use debug.vim from pymode):

        vim -u <path_to_pymode>/debug.vim

   And try to repeat your case. If no error occurs, seems like problem isn't in
   the plugin.

2. Type `:PymodeTroubleshooting` and fix any warnings or copy the output and
   send it to me. (For example, by creating a [new github issue](
   https://github.com/python-mode/python-mode/issues/new) if one does
   not already exist for the problem).

# Frequent problems

Read this section before opening an issue on the tracker.

## Python 3 syntax

By default python-mode uses python 2 syntax checking. To enable python 3 syntax
checking (e.g. for async) add:

    let g:pymode_python = 'python3'

To your vimrc or exrc file.

# Documentation

Documentation is available in your vim `:help pymode`.

# Bugtracker

If you have any suggestions, bug reports or annoyances please report them to
the issue tracker at:  
<https://github.com/python-mode/python-mode/issues>

# Contributing

* Kirill Klenov (<https://github.com/klen>)
* Felipe Vieira (<https://github.com/fmv1992>)

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
