""" Pylama integration. """

import vim # noqa
from .utils import pymode_message, silence_stderr

import os.path


def code_check():
    """ Run pylama and check current file.

    :return bool:

    """

    from pylama.main import parse_options
    from pylama.tasks import check_path
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

    code = '\n'.join(vim.current.buffer)

    with silence_stderr():
        errors = check_path(path, options=options, code=code)
    sort_rules = vim.eval('g:pymode_lint_sort')

    def __sort(e):
        try:
            return sort_rules.index(e.get('type'))
        except ValueError:
            return 999

    if sort_rules:
        errors = sorted(errors, key=__sort)

    for e in errors:
        e['bufnr'] = b.number

    vim.command(
        'call g:PymodeLocList.current().extend(%s)' % json.dumps(errors))
