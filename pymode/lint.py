""" Pylama integration. """

import vim # noqa
import os.path


def code_check():
    """ Run pylama and check current file. """

    from .pylama.main import parse_options
    from .pylama.tasks import check_path
    import json

    b = vim.current.buffer
    root = vim.eval('getcwd()')
    linters = vim.eval('g:pymode_lint_checkers')
    ignore = vim.eval('g:pymode_lint_ignore')
    select = vim.eval('g:pymode_lint_select')

    options = parse_options(
        ignore=ignore, select=select, linters=linters)

    path = b.name
    if root:
        path = os.path.relpath(path, root)

    errors = check_path(path, options=options)
    vim.command('call setqflist(%s)' % json.dumps(errors))
