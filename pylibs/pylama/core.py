""" Pylama core functionality. Get params and runs the checkers.
"""
import logging
import re

from . import utils


#: A default checkers
DEFAULT_LINTERS = 'pep8', 'pyflakes', 'mccabe'

#: The skip pattern
SKIP_PATTERN = '# noqa'

# Parse a modelines
MODELINE_RE = re.compile(
    r'^\s*#\s+(?:pymode\:)?((?:lint[\w_]*=[^:\n\s]+:?)+)', re.I | re.M)

# Setup a logger
LOGGER = logging.getLogger('pylama')
STREAM = logging.StreamHandler()
LOGGER.addHandler(STREAM)


def run(path, ignore=None, select=None, linters=DEFAULT_LINTERS, config=None,
        **meta):
    """ Run code checking for path.

    :return errors: list of dictionaries with error's information

    """
    errors = []

    try:
        with open(path, 'rU') as f:
            code = f.read() + '\n\n'

            params = prepare_params(
                parse_modeline(code), config, ignore=ignore, select=select
            )

            for line in code.split('\n'):
                params['skip'].append(line.endswith(SKIP_PATTERN))

            if not params['lint']:
                return errors

            for lint in linters:
                try:
                    linter = getattr(utils, lint)
                except AttributeError:
                    LOGGER.warning("Linter `%s` not found.", lint)
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
                    try:
                        if not params['skip'][e['lnum']]:
                            errors.append(e)
                    except IndexError:
                        continue

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
            text=e.args[0] + ' [%s]' % lint
        ))

    except Exception:
        import traceback
        logging.debug(traceback.format_exc())

    errors = [er for er in errors if filter_errors(er, **params)]
    return sorted(errors, key=lambda x: x['lnum'])


def parse_modeline(code):
    """ Parse modeline params from file.

    :return dict: Linter params.

    """
    seek = MODELINE_RE.search(code)
    if seek:
        return dict(v.split('=') for v in seek.group(1).split(':'))

    return dict()


def prepare_params(*configs, **params):
    """ Prepare and merge a params from modeline or config.

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
    params['skip'] = [False]
    params.setdefault('lint', 1)
    return params


def filter_errors(e, select=None, ignore=None, **params):
    """ Filter a erros by select and ignore lists.

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
