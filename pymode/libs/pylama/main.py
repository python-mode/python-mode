"""Pylama's shell support."""

from __future__ import absolute_import, with_statement

import sys
from os import walk, path as op

from .config import parse_options, CURDIR, setup_logger
from .core import LOGGER, run
from .async import check_async


def check_path(options, rootdir=None, candidates=None, code=None):
    """Check path.

    :param rootdir: Root directory (for making relative file paths)
    :param options: Parsed pylama options (from pylama.config.parse_options)

    :returns: (list) Errors list

    """
    if not candidates:
        candidates = []
        for path_ in options.paths:
            path = op.abspath(path_)
            if op.isdir(path):
                for root, _, files in walk(path):
                    candidates += [op.relpath(op.join(root, f), CURDIR) for f in files]
            else:
                candidates.append(path)

    if rootdir is None:
        rootdir = path if op.isdir(path) else op.dirname(path)

    paths = []
    for path in candidates:

        if not options.force and not any(l.allow(path) for _, l in options.linters):
            continue

        if not op.exists(path):
            continue

        paths.append(path)

    if options.async:
        return check_async(paths, options, rootdir)

    errors = []
    for path in paths:
        errors += run(path=path, code=code, rootdir=rootdir, options=options)
    return errors


def shell(args=None, error=True):
    """Endpoint for console.

    Parse a command arguments, configuration files and run a checkers.

    :return list: list of errors
    :raise SystemExit:

    """
    if args is None:
        args = sys.argv[1:]

    options = parse_options(args)
    setup_logger(options)
    LOGGER.info(options)

    # Install VSC hook
    if options.hook:
        from .hook import install_hook
        for path in options.paths:
            return install_hook(path)

    return process_paths(options, error=error)


def process_paths(options, candidates=None, error=True):
    """Process files and log errors."""
    errors = check_path(options, rootdir=CURDIR, candidates=candidates)

    if options.format in ['pycodestyle', 'pep8']:
        pattern = "%(filename)s:%(lnum)s:%(col)s: %(text)s"
    elif options.format == 'pylint':
        pattern = "%(filename)s:%(lnum)s: [%(type)s] %(text)s"
    else:  # 'parsable'
        pattern = "%(filename)s:%(lnum)s:%(col)s: [%(type)s] %(text)s"

    for er in errors:
        if options.abspath:
            er._info['filename'] = op.abspath(er.filename)
        LOGGER.warning(pattern, er._info)

    if error:
        sys.exit(int(bool(errors)))

    return errors


if __name__ == '__main__':
    shell()

# pylama:ignore=F0001
