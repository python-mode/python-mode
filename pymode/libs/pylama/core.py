""" Pylama's core functionality.

Prepare params, check a modeline and run the checkers.

"""
import re

import logging

from .config import process_value, LOGGER
from .lint.extensions import LINTERS


#: The skip pattern
SKIP_PATTERN = re.compile(r'# *noqa\b', re.I).search

# Parse a modelines
MODELINE_RE = re.compile(
    r'^\s*#\s+(?:pylama:)\s*((?:[\w_]*=[^:\n\s]+:?)+)',
    re.I | re.M)


def run(path, code=None, options=None):
    """ Run a code checkers with given params.

    :return errors: list of dictionaries with error's information

    """
    errors = []
    params = dict(ignore=options.ignore, select=options.select)
    fileconfig = dict()
    for mask in options.file_params:
        if mask.match(path):
            fileconfig.update(options.file_params[mask])

    try:
        with CodeContext(code, path) as ctx:
            code = ctx.code
            params = prepare_params(parse_modeline(code), fileconfig, options)

            if params.get('skip'):
                return errors

            for item in options.linters:

                if not isinstance(item, tuple):
                    item = (item, LINTERS.get(item))

                name, linter = item

                if not linter or not linter.allow(path):
                    continue

                LOGGER.info("Run %s", name)
                meta = options.linter_params.get(name, dict())
                result = linter.run(path, code=code, **meta)
                for e in result:
                    e['linter'] = name
                    e['col'] = e.get('col') or 0
                    e['lnum'] = e.get('lnum') or 0
                    e['type'] = e.get('type') or 'E'
                    e['text'] = "%s [%s]" % (
                        e.get('text', '').strip().split('\n')[0], name)
                    e['filename'] = path or ''
                    errors.append(e)

    except IOError as e:
        LOGGER.debug("IOError %s", e)
        errors.append(dict(
            lnum=0, type='E', col=0, text=str(e), filename=path or ''))

    except SyntaxError as e:
        LOGGER.debug("SyntaxError %s", e)
        errors.append(dict(
            lnum=e.lineno or 0, type='E', col=e.offset or 0,
            text=e.args[0] + ' [%s]' % name, filename=path or ''
        ))

    except Exception as e:
        import traceback
        LOGGER.info(traceback.format_exc())

    errors = [er for er in errors if filter_errors(er, **params)]

    if code and errors:
        errors = filter_skiplines(code, errors)

    return sorted(errors, key=lambda x: x['lnum'])


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
    params = dict(ignore=options.ignore, select=options.select, skip=False)

    for config in filter(None, [modeline, fileconfig]):
        for key in ('ignore', 'select'):
            params[key] += process_value(key, config.get(key, []))
        params['skip'] = bool(int(config.get('skip', False)))

    params['ignore'] = set(params['ignore'])
    params['select'] = set(params['select'])

    return params


def filter_errors(e, select=None, ignore=None, **params):
    """ Filter a erros by select and ignore options.

    :return bool:

    """
    if select:
        for s in select:
            if e['text'].startswith(s):
                return True

    if ignore:
        for s in ignore:
            if e['text'].startswith(s):
                return False

    return True


def filter_skiplines(code, errors):
    """ Filter lines by `noqa`.

    :return list: A filtered errors

    """
    if not errors:
        return errors

    enums = set(er['lnum'] for er in errors)
    removed = set([
        num for num, l in enumerate(code.split('\n'), 1)
        if num in enums and SKIP_PATTERN(l)
    ])

    if removed:
        errors = [er for er in errors if not er['lnum'] in removed]

    return errors


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
