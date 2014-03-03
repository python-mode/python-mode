""" Pylama integration. """

from .environment import env
from .utils import silence_stderr

import os.path


def code_check():
    """ Run pylama and check current file.

    :return bool:

    """

    with silence_stderr():

        from pylama.main import parse_options
        from pylama.tasks import check_path

        if not env.curbuf.name:
            return env.stop()

        options = parse_options(
            ignore=env.var('g:pymode_lint_ignore'),
            select=env.var('g:pymode_lint_select'),
            linters=env.var('g:pymode_lint_checkers'),
        )

        path = os.path.relpath(env.curbuf.name, env.curdir)
        env.debug("Start code check: ", path)

        if getattr(options, 'skip', None) and any(p.match(path) for p in options.skip): # noqa
            env.message('Skip code checking.')
            env.debug("Skipped")
            return env.stop()

        if env.options.get('debug'):
            from pylama.core import LOGGER, logging
            LOGGER.setLevel(logging.DEBUG)

        errors = check_path(
            path, options=options, code='\n'.join(env.curbuf) + '\n')

    env.debug("Find errors: ", len(errors))
    sort_rules = env.var('g:pymode_lint_sort')

    def __sort(e):
        try:
            return sort_rules.index(e.get('type'))
        except ValueError:
            return 999

    if sort_rules:
        env.debug("Find sorting: ", sort_rules)
        errors = sorted(errors, key=__sort)

    for e in errors:
        e['bufnr'] = env.curbuf.number

    env.run('g:PymodeLocList.current().extend', errors)
