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
    """Fix PEP8 errors in current buffer using ruff format.

    pymode: uses it in command PymodeLintAuto with pymode#lint#auto()

    """
    from .ruff_integration import run_ruff_format, check_ruff_available

    if not check_ruff_available():
        vim.command('echoerr "Ruff is not available. Please install ruff: pip install ruff"')
        return

    current_buffer = vim.current.buffer
    file_path = current_buffer.name
    
    if not file_path:
        vim.command('echoerr "Cannot format unsaved buffer"')
        return

    # Get current buffer content
    content = '\n'.join(current_buffer) + '\n'
    
    # Run ruff format
    formatted_content = run_ruff_format(file_path, content)
    
    if formatted_content is not None and formatted_content != content:
        # Update buffer with formatted content
        lines = formatted_content.rstrip('\n').splitlines()
        if not lines:
            lines = ['']
        current_buffer[:] = lines
        
        # Mark buffer as modified so Vim knows it can be written
        vim.command('setlocal modified')
        vim.command('echom "Ruff format completed"')
    else:
        vim.command('echom "No formatting changes needed"')


def get_documentation():
    """Search documentation and append to current buffer."""
    from io import StringIO

    sys.stdout, _ = StringIO(), sys.stdout
    help(vim.eval('a:word'))
    sys.stdout, out = _, sys.stdout.getvalue()
    vim.current.buffer.append(str(out).splitlines(), 0)
