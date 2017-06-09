"""Pylama integration."""

from .environment import env
from .utils import silence_stderr

import os
import os.path
import re
import subprocess
import tempfile

from pylama.errors import Error as LintError
from pylama.lint.extensions import LINTERS

try:
    from pylama.lint.pylama_pylint import Linter
    LINTERS['pylint'] = Linter()
except Exception: # noqa
    pass


def __maybe_list_to_str(x):
    """Convert list or string to str."""
    if isinstance(x, str):
        return x
    else:
        return ','.join(x)

__PARSE_PYLAMA_MESSSAGE_RE = re.compile(
    '^(?P<filename>.*?):(?P<lnum>\d*):(((?P<col>\d*):)| (\[(?P<type>.*?)\])) (?P<text>.*)$')
__PARSE_PYLAMA_TEXT_RE = re.compile(
    '^(?P<text>.*) \[(?P<linter>.*?)\]$')


def _external_python_code_check(python_binary, linters, ignore, select, linter_options):
    path = os.path.relpath(env.curbuf.name, env.curdir)
    env.debug("Start code check: ", path)

    check_path_command_args = [
        python_binary, '-m', 'pylama', path,
        '--linters', __maybe_list_to_str(linters),
        '--force',
        '--ignore', __maybe_list_to_str(ignore),
        '--select', __maybe_list_to_str(select),
    ]
    env.debug("Linter options: ", linter_options)

    options_file = None
    try:
        if linter_options:
            with tempfile.NamedTemporaryFile('w', delete=False) as f:
                options_file = f.name
                for linter, opts in linter_options.items():
                    f.write('[pylama:{linter!s}]\n'.format(linter=linter))
                    for param, value in opts.items():
                        f.write('{param!s}={value!s}\n'.format(
                            param=param, value=value))

                check_path_command_args += ['--options', options_file]

        env.debug("Check path args: ", check_path_command_args)
        check_path_process = subprocess.Popen(
            check_path_command_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)

        stdout, stderr = check_path_process.communicate()
    finally:
        if options_file is not None:
            os.remove(options_file)

    errors = []
    for line in stdout.splitlines():
        message_match = __PARSE_PYLAMA_MESSSAGE_RE.match(line)
        if message_match is not None:
            full_message_text = message_match.group('text')
            error_kwargs = {
                'filename': message_match.group('filename'),
            }
            if message_match.group('lnum'):
                error_kwargs['lnum'] = int(message_match.group('lnum'))
            if message_match.group('col'):
                error_kwargs['col'] = int(message_match.group('col'))
            if message_match.group('type') is not None:
                error_kwargs['type'] = message_match.group('type')

            linter_match = __PARSE_PYLAMA_TEXT_RE.match(full_message_text)
            if linter_match is None:
                error_kwargs['text'] = full_message_text
            else:
                error_kwargs['text'] = linter_match.group('text')
                error_kwargs['linter'] = linter_match.group('linter')

            errors.append(LintError(**error_kwargs))
    return errors


def _internal_python_code_check(linters, ignore, select, linter_options):
    from pylama.core import run
    from pylama.main import parse_options

    if not env.curbuf.name:
        return env.stop()

    options = parse_options(
        linters=linters, force=1,
        ignore=ignore,
        select=select,
    )

    for linter, opts in linter_options.items():
        if opts:
            options.linters_params[linter] = options.linters_params.get(linter, {})
            options.linters_params[linter].update(opts)

    env.debug(options)

    path = os.path.relpath(env.curbuf.name, env.curdir)
    env.debug("Start code check: ", path)

    if getattr(options, 'skip', None) and any(p.match(path) for p in options.skip): # noqa
        env.message('Skip code checking.')
        env.debug("Skipped")
        return env.stop()

    if env.options.get('debug'):
        from pylama.core import LOGGER, logging
        LOGGER.setLevel(logging.DEBUG)

    errors = run(path, code='\n'.join(env.curbuf) + '\n', options=options)
    return errors


def code_check():
    """Run pylama and check current file.

    :return bool:

    """
    with silence_stderr():
        if not env.curbuf.name:
            return env.stop()

        linters = env.var('g:pymode_lint_checkers')
        env.debug(linters)
        ignore = env.var('g:pymode_lint_ignore')
        select = env.var('g:pymode_lint_select')

        linter_options = {}
        for linter in linters:
            opts = env.var('g:pymode_lint_options_%s' % linter, silence=True)
            if opts:
                linter_options[linter] = opts

        python_binary = env.var('g:pymode_lint_external_python', silence=True)
        if python_binary:
            errors = _external_python_code_check(
                python_binary=python_binary,
                linters=linters,
                ignore=ignore,
                select=select,
                linter_options=linter_options)
        else:
            errors = _internal_python_code_check(
                linters=linters,
                ignore=ignore,
                select=select,
                linter_options=linter_options)

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
