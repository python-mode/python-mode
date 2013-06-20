""" Pylama core functionality. Get params and runs a checkers.
"""
import logging
import re

from . import utils


DEFAULT_LINTERS = 'pep8', 'pyflakes', 'mccabe'
LOGGER = logging.getLogger('pylama')
MODERE = re.compile(r'^\s*#\s+(?:pymode\:)?((?:lint[\w_]*=[^:\n\s]+:?)+)',
                    re.I | re.M)
SKIP_PATTERN = '# noqa'
STREAM = logging.StreamHandler()

LOGGER.addHandler(STREAM)


def run(path, ignore=None, select=None, linters=DEFAULT_LINTERS, config=None,
        **meta):
    """ Run code checking for path.

    :return errors: list of dictionaries with error's information

    """
    errors = []
    ignore = ignore and list(ignore) or []
    select = select and list(select) or []

    try:
        with open(path, 'rU') as f:
            code = f.read() + '\n\n'
            params = config or __parse_modeline(code)
            params['skip'] = [False]

            for line in code.split('\n'):
                params['skip'].append(line.endswith(SKIP_PATTERN))

            if params.get('lint_ignore'):
                ignore += params.get('lint_ignore').split(',')

            if params.get('lint_select'):
                select += params.get('lint_select').split(',')

            if params.get('lint'):
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

    errors = [er for er in errors if __ignore_error(er, select, ignore)]
    return sorted(errors, key=lambda x: x['lnum'])


def __parse_modeline(code):
    """ Parse modeline params from file.

    :return dict: Linter params.

    """
    seek = MODERE.search(code)
    params = dict(lint=1)
    if seek:
        params = dict(v.split('=') for v in seek.group(1).split(':'))
        params['lint'] = int(params.get('lint', 1))
    return params


def __ignore_error(e, select, ignore):
    for s in select:
        if e['text'].startswith(s):
            return True
    for i in ignore:
        if e['text'].startswith(i):
            return False
    return True
