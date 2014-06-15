""" Pylama's core functionality.

Prepare params, check a modeline and run the checkers.

"""
import re

import logging
from collections import defaultdict

from .config import process_value, LOGGER
from .lint.extensions import LINTERS
from .errors import DUPLICATES, Error


#: The skip pattern
SKIP_PATTERN = re.compile(r'# *noqa\b', re.I).search

# Parse a modelines
MODELINE_RE = re.compile(
    r'^\s*#\s+(?:pylama:)\s*((?:[\w_]*=[^:\n\s]+:?)+)',
    re.I | re.M)


def run(path='', code=None, options=None):
    """ Run a code checkers with given params.

    :return errors: list of dictionaries with error's information

    """
    errors = []
    fileconfig = dict()
    params = dict()
    linters = LINTERS
    linters_params = dict()

    if options:
        linters = options.linters
        linters_params = options.linters_params
        for mask in options.file_params:
            if mask.match(path):
                fileconfig.update(options.file_params[mask])

    try:
        with CodeContext(code, path) as ctx:
            code = ctx.code
            params = prepare_params(parse_modeline(code), fileconfig, options)
            LOGGER.debug('Checking params: %s', params)

            if params.get('skip'):
                return errors

            for item in linters:

                if not isinstance(item, tuple):
                    item = (item, LINTERS.get(item))

                lname, linter = item

                if not linter:
                    continue

                lparams = linters_params.get(lname, dict())
                LOGGER.info("Run %s %s", lname, lparams)

                for er in linter.run(
                        path, code=code, ignore=params.get("ignore", set()),
                        select=params.get("select", set()), params=lparams):
                    errors.append(Error(filename=path, linter=lname, **er))

    except IOError as e:
        LOGGER.debug("IOError %s", e)
        errors.append(Error(text=str(e), filename=path, linter=lname))

    except SyntaxError as e:
        LOGGER.debug("SyntaxError %s", e)
        errors.append(
            Error(linter=lname, lnum=e.lineno, col=e.offset, text=e.args[0],
                  filename=path))

    except Exception as e:
        import traceback
        LOGGER.info(traceback.format_exc())

    errors = filter_errors(errors, **params)

    errors = list(remove_duplicates(errors))

    if code and errors:
        errors = filter_skiplines(code, errors)

    return sorted(errors, key=lambda e: e.lnum)


def parse_modeline(code):
    """ Parse params from file's modeline.

    :return dict: Linter params.

    """
    seek = MODELINE_RE.search(code)
    if seek:
        return dict(v.split('=') for v in seek.group(1).split(':'))

    return dict()


def prepare_params(modeline, fileconfig, options):
    """ Prepare and merge a params from modelines and configs.

    :return dict:

    """
    params = dict(skip=False, ignore=[], select=[])
    if options:
        params['ignore'] = options.ignore
        params['select'] = options.select

    for config in filter(None, [modeline, fileconfig]):
        for key in ('ignore', 'select'):
            params[key] += process_value(key, config.get(key, []))
        params['skip'] = bool(int(config.get('skip', False)))

    params['ignore'] = set(params['ignore'])
    params['select'] = set(params['select'])

    return params


def filter_errors(errors, select=None, ignore=None, **params):
    """ Filter a erros by select and ignore options.

    :return bool:

    """
    select = select or []
    ignore = ignore or []

    for e in errors:
        for s in select:
            if e.number.startswith(s):
                yield e
                break
        else:
            for s in ignore:
                if e.number.startswith(s):
                    break
            else:
                yield e


def filter_skiplines(code, errors):
    """ Filter lines by `noqa`.

    :return list: A filtered errors

    """
    if not errors:
        return errors

    enums = set(er.lnum for er in errors)
    removed = set([
        num for num, l in enumerate(code.split('\n'), 1)
        if num in enums and SKIP_PATTERN(l)
    ])

    if removed:
        errors = [er for er in errors if er.lnum not in removed]

    return errors


def remove_duplicates(errors):
    """ Remove same errors from others linters. """
    passed = defaultdict(list)
    for error in errors:
        key = error.linter, error.number
        if key in DUPLICATES:
            if key in passed[error.lnum]:
                continue
            passed[error.lnum] = DUPLICATES[key]
        yield error


class CodeContext(object):

    """ Read file if code is None. """

    def __init__(self, code, path):
        """ Init context. """
        self.code = code
        self.path = path
        self._file = None

    def __enter__(self):
        """ Open file and read a code. """
        if self.code is None:
            self._file = open(self.path, 'rU')
            self.code = self._file.read()
        return self

    def __exit__(self, t, value, traceback):
        """ Close opened file. """
        if self._file is not None:
            self._file.close()

        if t and LOGGER.level == logging.DEBUG:
            LOGGER.debug(traceback)
