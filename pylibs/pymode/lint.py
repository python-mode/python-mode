""" Pylama support. """
from __future__ import absolute_import

import fnmatch
import json
import locale
from os import path as op
from re import compile as re

from pylama.core import run
from pylama.inirama import Namespace
from pylama.main import prepare_params

from . import interface
from .queue import add_task


try:
    locale.setlocale(locale.LC_CTYPE, "C")
except AttributeError:
    pass


def check_file():
    """ Check current buffer. """
    checkers = interface.get_option('lint_checker').split(',')
    buf = interface.get_current_buffer()

    # Check configuration from `pymode.ini`
    curdir = interface.eval_code('getcwd()')
    config = Namespace()
    config.default_section = 'main'
    config.read(op.join(curdir, 'pylama.ini'), op.join(curdir, 'pymode.ini'))

    ignore = set([
        i for i in (
            interface.get_option('lint_ignore').split(',') +
            interface.get_var('lint_ignore').split(',') +
            config.default.get('ignore', '').split(',')
        ) if i
    ])

    select = set([
        s for s in (
            interface.get_option('lint_select').split(',') +
            interface.get_var('lint_select').split(',') +
            config.default.get('select', '').split(',')
        ) if s
    ])

    complexity = int(interface.get_option('lint_mccabe_complexity') or 0)

    params = dict()
    relpath = op.relpath(buf.name, curdir)
    for mask in config.sections:
        mask_re = re(fnmatch.translate(mask))
        if mask_re.match(relpath):
            params.update(prepare_params(config[mask]))

    if relpath in config:
        params = prepare_params(config[relpath])

    add_task(
        run_checkers,
        callback=parse_result,
        title='Code checking',

        # params
        checkers=checkers, ignore=ignore, buf=buf, select=select,
        complexity=complexity, config=params,
    )


def run_checkers(checkers=None, ignore=None, buf=None, select=None,
                 complexity=None, callback=None, config=None):
    """ Run pylama code.

    :return list: errors

    """
    pylint_options = '--rcfile={0} -r n'.format(
        interface.get_var('lint_config')).split()

    return run(
        buf.name, ignore=ignore, select=select, linters=checkers,
        pylint=pylint_options, complexity=complexity, config=config)


def parse_result(result, buf=None, **kwargs):
    """ Parse results. """
    interface.command('let g:qf_list = ' + json.dumps(result))
    interface.command('call pymode#lint#Parse({0})'.format(buf.number))

# pymode:lint_ignore=W0622
