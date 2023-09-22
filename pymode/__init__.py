"""Pymode support functions."""

import sys
from importlib.machinery import PathFinder as _PathFinder

import vim  # noqa

if not hasattr(vim, 'find_module'):
    try:
        vim.find_module = _PathFinder.find_module  # deprecated
    except AttributeError:
        def _find_module(package_name):
            spec = _PathFinder.find_spec(package_name)
            return spec.loader if spec else None
        vim.find_module = _find_module


def auto():
    """Fix PEP8 erorrs in current buffer.

    pymode: uses it in command PymodeLintAuto with pymode#lint#auto()

    """
    from .autopep8 import fix_file

    class Options(object):
        aggressive = 1
        diff = False
        experimental = True
        ignore = vim.eval('g:pymode_lint_ignore')
        in_place = True
        indent_size = int(vim.eval('&tabstop'))
        line_range = None
        hang_closing = False
        max_line_length = int(vim.eval('g:pymode_options_max_line_length'))
        pep8_passes = 100
        recursive = False
        select = vim.eval('g:pymode_lint_select')
        verbose = 0

    fix_file(vim.current.buffer.name, Options)


def get_documentation():
    """Search documentation and append to current buffer."""
    from io import StringIO

    sys.stdout, _ = StringIO(), sys.stdout
    help(vim.eval('a:word'))
    sys.stdout, out = _, sys.stdout.getvalue()
    vim.current.buffer.append(str(out).splitlines(), 0)
