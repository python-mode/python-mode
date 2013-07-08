""" Pylama shell integration.
"""
from __future__ import absolute_import, with_statement

import fnmatch
import logging
import re
import sys
from argparse import ArgumentParser
from os import getcwd, walk, path as op

from . import utils, version
from .core import DEFAULT_LINTERS, LOGGER, STREAM


DEFAULT_COMPLEXITY = 10


def shell(args=None, error=True):
    """ Endpoint for console.

    :return list: list of errors
    :raise SystemExit:

    """
    curdir = getcwd()
    if args is None:
        args = sys.argv[1:]

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
        help=(
            "Select linters. (comma-separated). Choices are %s."
            % ','.join(s for s in utils.__all__)
        ))
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
        "--async", action="store_true",
        help="Enable async mode. Usefull for checking a lot of files. "
             "Dont supported with pylint.")
    parser.add_argument(
        "--options", "-o", default=op.join(curdir, 'pylama.ini'),
        help="Select configuration file. By default is '<CURDIR>/pylama.ini'")
    options = parser.parse_args(args)
    actions = dict((a.dest, a) for a in parser._actions)

    # Read options from configuration file
    from .inirama import Namespace

    config = Namespace()
    config.default_section = 'main'
    config.read(options.options)
    for k, v in config.default.items():
        action = actions.get(k)
        if action:
            LOGGER.info('Find option %s (%s)', k, v)
            name, value = action.dest, action.type(v)\
                if callable(action.type) else v
            if action.const:
                value = bool(int(value))
            setattr(options, name, value)

    # Setup LOGGER
    LOGGER.setLevel(logging.INFO if options.verbose else logging.WARN)
    if options.report:
        LOGGER.removeHandler(STREAM)
        LOGGER.addHandler(logging.FileHandler(options.report, mode='w'))
    LOGGER.info('Try to read configuration from: ' + options.options)

    # Install VSC hook
    if options.hook:
        from .hook import install_hook
        install_hook(options.path)

    else:

        paths = [options.path]

        if op.isdir(options.path):
            paths = []
            for root, _, files in walk(options.path):
                paths += [
                    op.relpath(op.join(root, f), curdir)
                    for f in files if f.endswith('.py')]

        return check_files(
            paths,
            async=options.async,
            rootpath=curdir,
            skip=options.skip,
            frmt=options.format,
            ignore=options.ignore,
            select=options.select,
            linters=options.linters,
            complexity=options.complexity,
            config=config,
            error=error,
        )


def check_files(paths, rootpath=None, skip=None, frmt="pep8", async=False,
                select=None, ignore=None, linters=DEFAULT_LINTERS,
                complexity=DEFAULT_COMPLEXITY, config=None, error=True):
    """ Check files.

    :return list: list of errors
    :raise SystemExit:

    """
    from .tasks import async_check_files

    rootpath = rootpath or getcwd()
    pattern = "%(rel)s:%(lnum)s:%(col)s: %(text)s"
    if frmt == 'pylint':
        pattern = "%(rel)s:%(lnum)s: [%(type)s] %(text)s"

    params = dict()
    if config:
        for key, section in config.sections.items():
            if key != config.default_section:
                mask = re.compile(fnmatch.translate(key))
                params[mask] = prepare_params(section)

    work_paths = []
    for path in paths:
        if skip and any(pattern.match(path) for pattern in skip):
            LOGGER.info('Skip path: %s', path)
            continue
        work_paths.append(path)

    errors = async_check_files(
        work_paths, async=async, rootpath=rootpath, ignore=ignore,
        select=select, linters=linters, complexity=complexity, params=params)

    for er in errors:
        LOGGER.warning(pattern, er)

    if error:
        sys.exit(int(bool(errors)))

    return errors


def prepare_params(section):
    """ Parse modeline params from configuration.

    :return dict: Linter params.

    """
    params = dict(section)
    params['lint'] = int(params.get('lint', 1))
    return params


if __name__ == '__main__':
    shell()
