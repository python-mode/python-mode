"""Pylama's core functionality.

Prepare params, check a modeline and run the checkers.
"""
import logging
import sys

import os.path as op
from .config import process_value, LOGGER, MODELINE_RE, SKIP_PATTERN, CURDIR
from .errors import Error, remove_duplicates
from .lint.extensions import LINTERS


def run(path='', code=None, rootdir=CURDIR, options=None):
    """Run code checkers with given params.

    :param path: (str) A file's path.
    :param code: (str) A code source
    :return errors: list of dictionaries with error's information

    """
    errors = []
    fileconfig = dict()
    linters = LINTERS
    linters_params = dict()
    lname = 'undefined'
    params = dict()
    path = op.relpath(path, rootdir)

    if options:
        linters = options.linters
        linters_params = options.linters_params
        for mask in options.file_params:
            if mask.match(path):
                fileconfig.update(options.file_params[mask])

        if options.skip and any(p.match(path) for p in options.skip):
            LOGGER.info('Skip checking for path: %s', path)
            return []

    try:
        with CodeContext(code, path) as ctx:
            code = ctx.code
            params = prepare_params(parse_modeline(code), fileconfig, options)
            LOGGER.debug('Checking params: %s', params)

            if params.get('skip'):
                return errors

            for item in params.get('linters') or linters:

                if not isinstance(item, tuple):
                    item = (item, LINTERS.get(item))

                lname, linter = item

                if not linter:
                    continue

                lparams = linters_params.get(lname, dict())
                LOGGER.info("Run %s %s", lname, lparams)

                linter_errors = linter.run(
                    path, code=code, ignore=params.get("ignore", set()),
                    select=params.get("select", set()), params=lparams)
                if linter_errors:
                    for er in linter_errors:
                        errors.append(Error(filename=path, linter=lname, **er))

    except IOError as e:
        LOGGER.debug("IOError %s", e)
        errors.append(Error(text=str(e), filename=path, linter=lname))

    except SyntaxError as e:
        LOGGER.debug("SyntaxError %s", e)
        errors.append(
            Error(linter='pylama', lnum=e.lineno, col=e.offset,
                  text='E0100 SyntaxError: {}'.format(e.args[0]),
                  filename=path))

    except Exception as e: # noqa
        import traceback
        LOGGER.info(traceback.format_exc())

    errors = filter_errors(errors, **params)  # noqa

    errors = list(remove_duplicates(errors))

    if code and errors:
        errors = filter_skiplines(code, errors)

    key = lambda e: e.lnum
    if options and options.sort:
        sort = dict((v, n) for n, v in enumerate(options.sort, 1))
        key = lambda e: (sort.get(e.type, 999), e.lnum)
    return sorted(errors, key=key)


def parse_modeline(code):
    """Parse params from file's modeline.

    :return dict: Linter params.

    """
    seek = MODELINE_RE.search(code)
    if seek:
        return dict(v.split('=') for v in seek.group(1).split(':'))

    return dict()


def prepare_params(modeline, fileconfig, options):
    """Prepare and merge a params from modelines and configs.

    :return dict:

    """
    params = dict(skip=False, ignore=[], select=[], linters=[])
    if options:
        params['ignore'] = list(options.ignore)
        params['select'] = list(options.select)

    for config in filter(None, [modeline, fileconfig]):
        for key in ('ignore', 'select', 'linters'):
            params[key] += process_value(key, config.get(key, []))
        params['skip'] = bool(int(config.get('skip', False)))

    params['ignore'] = set(params['ignore'])
    params['select'] = set(params['select'])

    return params


def filter_errors(errors, select=None, ignore=None, **params):
    """Filter errors by select and ignore options.

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
    """Filter lines by `noqa`.

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


class CodeContext(object):
    """Read file if code is None. """

    def __init__(self, code, path):
        """ Init context. """
        self.code = code
        self.path = path
        self._file = None

    def __enter__(self):
        """ Open a file and read it. """
        if self.code is None:
            LOGGER.info("File is reading: %s", self.path)
            if sys.version_info >= (3, ):
                # 'U' mode is deprecated in python 3
                mode = 'r'
            else:
                mode = 'rU'
            self._file = open(self.path, mode)
            self.code = self._file.read()
        return self

    def __exit__(self, t, value, traceback):
        """ Close the file which was opened. """
        if self._file is not None:
            self._file.close()

        if t and LOGGER.level == logging.DEBUG:
            LOGGER.debug(traceback)

# pylama:ignore=R0912,D210,F0001
