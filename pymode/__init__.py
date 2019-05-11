"""Pymode support functions."""

from __future__ import absolute_import

import sys
import vim  # noqa
try:
    from importlib.machinery import PathFinder as _PathFinder
    if not hasattr(vim, 'find_module'):
        vim.find_module = _PathFinder.find_module
except ImportError:
    pass

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
    from ._compat import StringIO

    sys.stdout, _ = StringIO(), sys.stdout
    help(vim.eval('a:word'))
    sys.stdout, out = _, sys.stdout.getvalue()
    vim.current.buffer.append(str(out).splitlines(), 0)
