""" Parse arguments from command line and configuration files. """
import fnmatch
import logging
from argparse import ArgumentParser, Namespace as Options
from os import getcwd, path
from re import compile as re

from . import version, utils
from .core import DEFAULT_LINTERS, LOGGER, STREAM
from .inirama import Namespace


DEFAULT_COMPLEXITY = 10
CURDIR = getcwd()
DEFAULT_INI_PATH = path.join(CURDIR, 'pylama.ini')


def parse_options(
        args=None, async=False, select='', ignore='', linters=DEFAULT_LINTERS,
        complexity=DEFAULT_COMPLEXITY, options=DEFAULT_INI_PATH):
    """ Parse options from command line and configuration files.

    :return argparse.Namespace:

    """
    parser = get_parser()
    actions = dict((a.dest, a) for a in parser._actions)
    options = Options(
        async=_Default(async), format=_Default('pep8'),
        select=_Default(select), ignore=_Default(ignore),
        report=_Default(None), verbose=_Default(False),
        linters=_Default(linters), complexity=_Default(complexity),
        options=_Default(options))

    if not (args is None):
        options = parser.parse_args(args)

    config = get_config(str(options.options))

    for k, v in config.default.items():
        value = getattr(options, k, _Default(None))
        if not isinstance(value, _Default):
            continue

        action = actions.get(k)
        LOGGER.info('Find option %s (%s)', k, v)
        name, value = action.dest, action.type(v)\
            if callable(action.type) else v
        if action.const:
            value = bool(int(value))
        setattr(options, name, value)

    opts = dict(options.__dict__.items())
    for name, value in opts.items():
        if isinstance(value, _Default):
            action = actions.get(name)
            if action and callable(action.type):
                value.value = action.type(value.value)

            setattr(options, name, value.value)

    options.file_params = dict()
    for k, s in config.sections.items():
        if k != config.default_section:
            mask = re(fnmatch.translate(k))
            options.file_params[mask] = dict(s)
            options.file_params[mask]['lint'] = int(
                options.file_params[mask].get('lint', 1)
            )

    return options


def setup_logger(options):
    """ Setup logger with options. """

    LOGGER.setLevel(logging.INFO if options.verbose else logging.WARN)
    if options.report:
        LOGGER.removeHandler(STREAM)
        LOGGER.addHandler(logging.FileHandler(options.report, mode='w'))
    LOGGER.info('Try to read configuration from: ' + options.options)


def get_parser():
    """ Make command parser for pylama.

    :return ArgumentParser:

    """
    split_csp_str = lambda s: list(
        set(i for i in s.strip().split(',') if i))

    parser = ArgumentParser(description="Code audit tool for python.")
    parser.add_argument(
        "path", nargs='?', default=_Default(CURDIR),
        help="Path on file or directory.")

    parser.add_argument(
        "--verbose", "-v", action='store_true', help="Verbose mode.")

    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + version)

    parser.add_argument(
        "--format", "-f", default=_Default('pep8'), choices=['pep8', 'pylint'],
        help="Error format.")

    parser.add_argument(
        "--select", "-s", default=_Default(''), type=split_csp_str,
        help="Select errors and warnings. (comma-separated)")

    parser.add_argument(
        "--linters", "-l", default=_Default(','.join(DEFAULT_LINTERS)),
        type=split_csp_str,
        help=(
            "Select linters. (comma-separated). Choices are %s."
            % ','.join(s for s in utils.__all__)
        ))

    parser.add_argument(
        "--ignore", "-i", default=_Default(''), type=split_csp_str,
        help="Ignore errors and warnings. (comma-separated)")

    parser.add_argument(
        "--skip", default=_Default(''),
        type=lambda s: [re(fnmatch.translate(p)) for p in s.split(',') if p],
        help="Skip files by masks (comma-separated, Ex. */messages.py)")

    parser.add_argument(
        "--complexity", "-c", default=_Default(DEFAULT_COMPLEXITY), type=int,
        help="Set mccabe complexity.")

    parser.add_argument("--report", "-r", help="Filename for report.")
    parser.add_argument(
        "--hook", action="store_true", help="Install Git (Mercurial) hook.")

    parser.add_argument(
        "--async", action="store_true",
        help="Enable async mode. Usefull for checking a lot of files. "
        "Dont supported with pylint.")

    parser.add_argument(
        "--options", "-o", default=_Default(DEFAULT_INI_PATH),
        help="Select configuration file. By default is '<CURDIR>/pylama.ini'")

    return parser


def get_config(ini_path=DEFAULT_INI_PATH):
    """ Load configuration from INI.

    :return Namespace:

    """
    config = Namespace()
    config.default_section = 'main'
    config.read(ini_path)

    return config


class _Default(object):

    def __init__(self, value):
        self.value = value

    def __getattr__(self, name):
        return getattr(self.value, name)

    def __str__(self):
        return str(self.value)


# lint_ignore=R0914,W0212,E1103,C901
