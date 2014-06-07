""" Pylama's shell support. """

from __future__ import absolute_import, with_statement

import sys
from os import walk, path as op

from .config import parse_options, CURDIR, setup_logger
from .core import LOGGER


def shell(args=None, error=True):
    """ Endpoint for console.

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
        return install_hook(options.path)

    paths = [options.path]

    if op.isdir(options.path):
        paths = []
        for root, _, files in walk(options.path):
            paths += [op.relpath(op.join(root, f), CURDIR) for f in files]

    return check_files(paths, options, error=error)


def check_files(paths, options, rootpath=None, error=True):
    """ Check files.

    :return list: list of errors
    :raise SystemExit:

    """
    from .tasks import async_check_files

    if rootpath is None:
        rootpath = CURDIR

    pattern = "%(rel)s:%(lnum)s:%(col)s: %(text)s"
    if options.format == 'pylint':
        pattern = "%(rel)s:%(lnum)s: [%(type)s] %(text)s"

    work_paths = []
    for path in paths:

        if not options.force and not any(l.allow(path) for _, l in options.linters): # noqa
            continue

        if not op.exists(path):
            continue

        if options.skip and any(p.match(path) for p in options.skip):
            LOGGER.info('Skip path: %s', path)
            continue
        work_paths.append(path)

    errors = async_check_files(work_paths, options, rootpath=rootpath)

    for er in errors:
        LOGGER.warning(pattern, er._info)

    if error:
        sys.exit(int(bool(errors)))

    return errors


if __name__ == '__main__':
    shell()
