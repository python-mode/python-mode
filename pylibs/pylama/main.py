from __future__ import (
    print_function, absolute_import, with_statement
)

import fnmatch
import logging
import re
import sys
from argparse import ArgumentParser
from os import getcwd, walk, path as op

from . import utils, version
from .inirama import Namespace


DEFAULT_LINTERS = 'pep8', 'pyflakes', 'mccabe'
DEFAULT_COMPLEXITY = 10
LOGGER = logging.Logger('pylama')
STREAM = logging.StreamHandler()
LOGGER.addHandler(STREAM)

SKIP_PATTERN = '# nolint'


def run(path, ignore=None, select=None, linters=DEFAULT_LINTERS, config=None,
        **meta):
    errors = []
    ignore = ignore and list(ignore) or []
    select = select and list(select) or []

    try:
        with open(path, 'rU') as f:
            code = f.read() + '\n\n'
            params = config or parse_modeline(code)
            params['skip'] = [False]
            for line in code.split('\n'):
                params['skip'].append(line.endswith(SKIP_PATTERN))

            if params.get('lint_ignore'):
                ignore += params.get('lint_ignore').split(',')

            if params.get('lint_select'):
                select += params.get('lint_select').split(',')

            if params.get('lint'):
                for lint in linters:
                    try:
                        linter = getattr(utils, lint)
                    except AttributeError:
                        logging.warning("Linter `{0}` not found.".format(lint))
                        continue

                    result = linter(path, code=code, **meta)
                    for e in result:
                        e['col'] = e.get('col') or 0
                        e['lnum'] = e.get('lnum') or 0
                        e['type'] = e.get('type') or 'E'
                        e['text'] = "{0} [{1}]".format((e.get(
                            'text') or '').strip()
                            .replace("'", "\"").split('\n')[0], lint)
                        e['filename'] = path or ''
                        if not params['skip'][e['lnum']]:
                            errors.append(e)

    except IOError as e:
        errors.append(dict(
            lnum=0,
            type='E',
            col=0,
            text=str(e)
        ))

    except SyntaxError as e:
        errors.append(dict(
            lnum=e.lineno or 0,
            type='E',
            col=e.offset or 0,
            text=e.args[0]
        ))

    except Exception:
        import traceback
        logging.error(traceback.format_exc())

    errors = [er for er in errors if _ignore_error(er, select, ignore)]
    return sorted(errors, key=lambda x: x['lnum'])


def _ignore_error(e, select, ignore):
    for s in select:
        if e['text'].startswith(s):
            return True
    for i in ignore:
        if e['text'].startswith(i):
            return False
    return True


def shell():
    curdir = getcwd()
    parser = ArgumentParser(description="Code audit tool for python.")
    parser.add_argument("path", nargs='?', default=curdir,
                        help="Path on file or directory.")
    parser.add_argument(
        "--verbose", "-v", action='store_true', help="Verbose mode.")
    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + version)

    split_csp_list = lambda s: list(set(i for i in s.split(',') if i))

    parser.add_argument(
        "--format", "-f", default='pep8', choices=['pep8', 'pylint'],
        help="Error format.")
    parser.add_argument(
        "--select", "-s", default='',
        type=split_csp_list,
        help="Select errors and warnings. (comma-separated)")
    parser.add_argument(
        "--linters", "-l", default=','.join(DEFAULT_LINTERS),
        type=split_csp_list,
        help="Select linters. (comma-separated)")
    parser.add_argument(
        "--ignore", "-i", default='',
        type=split_csp_list,
        help="Ignore errors and warnings. (comma-separated)")
    parser.add_argument(
        "--skip", default='',
        type=lambda s: [re.compile(fnmatch.translate(p))
                        for p in s.split(',')],
        help="Skip files by masks (comma-separated, Ex. */messages.py)")
    parser.add_argument("--complexity", "-c", default=DEFAULT_COMPLEXITY,
                        type=int, help="Set mccabe complexity.")
    parser.add_argument("--report", "-r", help="Filename for report.")
    parser.add_argument("--hook", action="store_true",
                        help="Install Git (Mercurial) hook.")
    parser.add_argument(
        "--options", "-o", default=op.join(curdir, 'pylama.ini'),
        help="Select configuration file. By default is '<CURDIR>/pylama.ini'")
    options = parser.parse_args()
    actions = dict((a.dest, a) for a in parser._actions)

    # Setup LOGGER
    LOGGER.setLevel(logging.INFO if options.verbose else logging.WARN)
    if options.report:
        LOGGER.removeHandler(STREAM)
        LOGGER.addHandler(logging.FileHandler(options.report, mode='w'))

    # Read options from configuration file
    config = Namespace()
    config.default_section = 'main'
    LOGGER.info('Try to read configuration from: ' + options.options)
    config.read(options.options)
    for k, v in config.default.items():
        action = actions.get(k)
        if action:
            LOGGER.info('Find option %s (%s)' % (k, v))
            name, value = action.dest, action.type(v)\
                if callable(action.type) else v
            setattr(options, name, value)

    # Install VSC hook
    if options.hook:
        from .hook import install_hook
        return install_hook(options.path)

    paths = [options.path]

    if op.isdir(options.path):
        paths = []
        for root, _, files in walk(options.path):
            paths += [op.join(root, f) for f in files if f.endswith('.py')]

    check_files(
        paths,
        rootpath=options.path,
        skip=options.skip,
        frmt=options.format,
        ignore=options.ignore,
        select=options.select,
        linters=options.linters,
        complexity=options.complexity,
        config=config,
    )


def check_files(paths, rootpath=None, skip=None, frmt="pep8",
                select=None, ignore=None, linters=DEFAULT_LINTERS,
                complexity=DEFAULT_COMPLEXITY, config=None):
    rootpath = rootpath or getcwd()
    pattern = "%(rel)s:%(lnum)s:%(col)s: %(text)s"
    if frmt == 'pylint':
        pattern = "%(rel)s:%(lnum)s: [%(type)s] %(text)s"

    params = dict()
    if config:
        for key, section in config.sections.items():
            if key != 'main':
                params[op.abspath(key)] = prepare_params(section)

    errors = []

    for path in paths:
        path = op.abspath(path)
        if any(pattern.match(path) for pattern in skip):
            LOGGER.info('Skip path: %s' % path)
            continue

        LOGGER.info("Parse file: %s" % path)
        errors = run(path, ignore=ignore, select=select, linters=linters,
                     complexity=complexity, config=params.get(path))
        for error in errors:
            try:
                error['rel'] = op.relpath(
                    error['filename'], op.dirname(rootpath))
                error['col'] = error.get('col', 1)
                LOGGER.warning(pattern, error)
            except KeyError:
                continue

    sys.exit(int(bool(errors)))


MODERE = re.compile(
    r'^\s*#\s+(?:pymode\:)?((?:lint[\w_]*=[^:\n\s]+:?)+)', re.I | re.M)


def parse_modeline(code):
    seek = MODERE.search(code)
    params = dict(lint=1)
    if seek:
        params = dict(v.split('=') for v in seek.group(1).split(':'))
        params['lint'] = int(params.get('lint', 1))
    return params


def prepare_params(section):
    params = dict(section)
    params['lint'] = int(params.get('lint', 1))
    return params


if __name__ == '__main__':
    shell()

# lint_ignore=R0914,C901,W0212
