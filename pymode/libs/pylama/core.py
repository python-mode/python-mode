""" Pylama's core functionality.

Prepare params, check a modeline and run the checkers.

"""
import logging
import re
import sys
from .lint.extensions import LINTERS

#: The skip pattern
SKIP_PATTERN = re.compile(r'# *noqa\b', re.I).search

# Parse a modelines
MODELINE_RE = re.compile(
    r'^\s*#\s+(?:pymode\:)?((?:lint[\w_]*=[^:\n\s]+:?)+)', re.I | re.M)

# Setup a logger
LOGGER = logging.getLogger('pylama')
STREAM = logging.StreamHandler(sys.stdout)
LOGGER.addHandler(STREAM)


def run(
        path, ignore=None, select=None, linters=None, config=None, code=None,
        **meta):
    """ Run a code checkers with given params.

    :return errors: list of dictionaries with error's information

    """
    errors = []
    linters = linters or LINTERS.items()
    params = dict(ignore=ignore, select=select)
    try:
        with CodeContext(code, path) as ctx:
            code = ctx.code
            params = prepare_params(
                parse_modeline(code), config, ignore=ignore, select=select
            )

            if not params['lint']:
                return errors

            for item in linters:

                if not isinstance(item, tuple):
                    item = (item, LINTERS.get(item))

                name, linter = item

                if not linter or not linter.allow(path):
                    continue

                result = linter.run(path, code=code, **meta)
                for e in result:
                    e['col'] = e.get('col') or 0
                    e['lnum'] = e.get('lnum') or 0
                    e['type'] = e.get('type') or 'E'
                    e['text'] = "{0} [{1}]".format((e.get(
                        'text') or '').strip()
                        .replace("'", "\"").split('\n')[0], name)
                    e['filename'] = path or ''
                    errors.append(e)

    except IOError as e:
        errors.append(dict(
            lnum=0, type='E', col=0, text=str(e), filename=path or ''))

    except SyntaxError as e:
        errors.append(dict(
            lnum=e.lineno or 0, type='E', col=e.offset or 0,
            text=e.args[0] + ' [%s]' % name, filename=path or ''
        ))

    except Exception:
        import traceback
        logging.debug(traceback.format_exc())

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


def prepare_params(*configs, **params):
    """ Prepare and merge a params from modelines and configs.

    :return dict:

    """
    params['ignore'] = list(params.get('ignore') or [])
    params['select'] = list(params.get('select') or [])

    for config in filter(None, configs):
        for key in ('ignore', 'select'):
            config.setdefault(key, config.get('lint_' + key, []))
            if not isinstance(config[key], list):
                config[key] = config[key].split(',')
            params[key] += config[key]
        params['lint'] = config.get('lint', 1)

    params['ignore'] = set(params['ignore'])
    params['select'] = set(params['select'])
    params.setdefault('lint', 1)
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
        self.code = code
        self.path = path
        self._file = None

    def __enter__(self):
        if self.code is None:
            self._file = open(self.path, 'rU')
            self.code = self._file.read() + '\n\n'
        return self

    def __exit__(self, t, value, traceback):
        if not self._file is None:
            self._file.close()

        if t and LOGGER.level == logging.DEBUG:
            LOGGER.debug(traceback)
