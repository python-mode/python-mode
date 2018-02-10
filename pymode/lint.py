"""Pylama integration."""

from .environment import env
from .utils import silence_stderr

import os.path


from pylama.lint.extensions import LINTERS

try:
    from pylama.lint.pylama_pylint import Linter
    LINTERS['pylint'] = Linter()
except Exception:  # noqa
    pass


def code_check():
    """Run pylama and check current file.

    :return bool:

    """
    with silence_stderr():

        from pylama.core import run
        from pylama.config import parse_options

        if not env.curbuf.name:
            return env.stop()

        linters = env.var('g:pymode_lint_checkers')
        env.debug(linters)

        # Fixed in v0.9.3: these two parameters may be passed as strings.
        # DEPRECATE: v:0.10.0: need to be set as lists.
        if isinstance(env.var('g:pymode_lint_ignore'), str):
            raise ValueError ('g:pymode_lint_ignore should have a list type')
        else:
            ignore = env.var('g:pymode_lint_ignore')
        if isinstance(env.var('g:pymode_lint_select'), str):
            raise ValueError ('g:pymode_lint_select should have a list type')
        else:
            select = env.var('g:pymode_lint_select')
        options = parse_options(
            linters=linters, force=1,
            ignore=ignore,
            select=select,
        )
        env.debug(options)

        for linter in linters:
            opts = env.var('g:pymode_lint_options_%s' % linter, silence=True)
            if opts:
                options.linters_params[linter] = options.linters_params.get(
                    linter, {})
                options.linters_params[linter].update(opts)

        path = os.path.relpath(env.curbuf.name, env.curdir)
        env.debug("Start code check: ", path)

        if getattr(options, 'skip', None) and any(p.match(path) for p in options.skip):  # noqa
            env.message('Skip code checking.')
            env.debug("Skipped")
            return env.stop()

        if env.options.get('debug'):
            from pylama.core import LOGGER, logging
            LOGGER.setLevel(logging.DEBUG)

        errors = run(path, code='\n'.join(env.curbuf) + '\n', options=options)

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
        e._info['bufnr'] = env.curbuf.number
        if e._info['col'] is None:
            e._info['col'] = 1

    env.run('g:PymodeLocList.current().extend', [e._info for e in errors])

# pylama:ignore=W0212,E1103
