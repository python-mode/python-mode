""" Pylama integration. """

import vim # noqa
from .utils import pymode_message

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

    if getattr(options, 'skip', None) and any(p.match(path) for p in options.skip): # noqa
        pymode_message('Skip code checking.')
        vim.command('return')
        return False

    errors = check_path(path, options=options)
    sort_rules = vim.eval('g:pymode_lint_sort')

    def sort(e):
        try:
            print(e.get('type'))
            return sort_rules.index(e.get('type'))
        except ValueError:
            return 999

    if sort_rules:
        print(sort_rules)
        errors = sorted(errors, key=sort)

    vim.command('call setqflist(%s)' % json.dumps(errors))
