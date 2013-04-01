import fnmatch
import re
import sys
from os import getcwd, walk, path as op

import logging
from argparse import ArgumentParser

from . import utils


default_linters = 'pep8', 'pyflakes', 'mccabe'
default_complexity = 10
logger = logging.Logger('pylama')
stream = logging.StreamHandler()
logger.addHandler(stream)

SKIP_PATTERN = '# nolint'


def run(path, ignore=None, select=None, linters=default_linters, **meta):  # nolint
    errors = []
    ignore = ignore and list(ignore) or []
    select = select and list(select) or []

    for lint in linters:
        try:
            linter = getattr(utils, lint)
        except AttributeError:
            logging.warning("Linter `{0}` not found.".format(lint))
            continue

        try:
            with open(path, "rU") as f:
                code = f.read() + '\n\n'
                params = parse_modeline(code)
                params['skip'] = [False]
                for line in code.split('\n'):
                    params['skip'].append(line.endswith(SKIP_PATTERN))

                if params.get('lint_ignore'):
                    ignore += params.get('lint_ignore').split(',')

                if params.get('lint_select'):
                    select += params.get('lint_select').split(',')

                if params.get('lint'):
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
            break

        except Exception as e:
            import traceback
            logging.error(traceback.format_exc())

    errors = [e for e in errors if _ignore_error(e, select, ignore)]
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
    parser = ArgumentParser(description="Code audit tool for python.")
    parser.add_argument("path", nargs='?', default=getcwd(),
                        help="Path on file or directory.")
    parser.add_argument(
        "--verbose", "-v", action='store_true', help="Verbose mode.")

    split_csp_list = lambda s: list(set(i for i in s.split(',') if i))

    parser.add_argument(
        "--format", "-f", default='pep8', choices=['pep8', 'pylint'],
        help="Error format.")
    parser.add_argument(
        "--select", "-s", default='',
        type=split_csp_list,
        help="Select errors and warnings. (comma-separated)")
    parser.add_argument(
        "--linters", "-l", default=','.join(default_linters),
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
    parser.add_argument("--complexity", "-c", default=default_complexity,
                        type=int, help="Set mccabe complexity.")
    parser.add_argument("--report", "-r", help="Filename for report.")
    parser.add_argument("--hook", action="store_true",
                        help="Install Git (Mercurial) hook.")
    args = parser.parse_args()

    # Setup logger
    logger.setLevel(logging.INFO if args.verbose else logging.WARN)
    if args.report:
        logger.removeHandler(stream)
        logger.addHandler(logging.FileHandler(args.report, mode='w'))

    if args.hook:
        from .hook import install_hook
        return install_hook(args.path)

    paths = [args.path]

    if op.isdir(args.path):
        paths = []
        for root, _, files in walk(args.path):
            paths += [op.join(root, f) for f in files if f.endswith('.py')]

    check_files(
        paths,
        rootpath=args.path,
        skip=args.skip,
        frmt=args.format,
        ignore=args.ignore,
        select=args.select,
        linters=args.linters,
        complexity=args.complexity,
    )


def check_files(paths, rootpath=None, skip=None, frmt="pep8",
                select=None, ignore=None, linters=default_linters,
                complexity=default_complexity):
    rootpath = rootpath or getcwd()
    pattern = "%(rel)s:%(lnum)s:%(col)s: %(text)s"
    if frmt == 'pylint':
        pattern = "%(rel)s:%(lnum)s: [%(type)s] %(text)s"

    errors = []
    for path in skip_paths(skip, paths):
        logger.info("Parse file: %s" % path)
        errors = run(path, ignore=ignore, select=select,
                     linters=linters, complexity=complexity)
        for error in errors:
            try:
                error['rel'] = op.relpath(
                    error['filename'], op.dirname(rootpath))
                error['col'] = error.get('col', 1)
                logger.warning(pattern, error)
            except KeyError:
                continue

    sys.exit(int(bool(errors)))


MODERE = re.compile(
    r'^\s*#\s+(?:pymode\:)?((?:lint[\w_]*=[^:\n\s]+:?)+)', re.I | re.M)


def skip_paths(skip, paths):
    for path in paths:
        if skip and any(pattern.match(path) for pattern in skip):
            continue
        yield path


def parse_modeline(code):
    seek = MODERE.search(code)
    params = dict(lint=1)
    if seek:
        params = dict(v.split('=') for v in seek.group(1).split(':'))
        params['lint'] = int(params.get('lint', 1))
    return params


if __name__ == '__main__':
    shell()
