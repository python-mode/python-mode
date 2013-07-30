""" Pylama support. """
from __future__ import absolute_import

import json
import locale

from pylama.main import parse_options
from pylama.tasks import check_path

from . import interface
from .queue import add_task


try:
    locale.setlocale(locale.LC_CTYPE, "C")
except AttributeError:
    pass


def check_file():
    """ Check current buffer. """
    buf = interface.get_current_buffer()

    linters = interface.get_option('lint_checker')
    ignore = interface.get_option('lint_ignore')
    select = interface.get_option('lint_select')
    complexity = interface.get_option('lint_mccabe_complexity') or '0'

    options = parse_options(
        ignore=ignore, select=select, complexity=complexity, linters=linters)

    add_task(
        run_checkers, callback=parse_result, title='Code checking', buf=buf,
        options=options,
    )


def run_checkers(callback=None, buf=None, options=None):
    """ Run pylama code.

    :return list: errors

    """
    pylint_options = '--rcfile={0} -r n'.format(
        interface.get_var('lint_config')).split()

    return check_path(buf.name, options=options, pylint=pylint_options)


def parse_result(result, buf=None, **kwargs):
    """ Parse results. """
    interface.command('let g:qf_list = ' + json.dumps(result))
    interface.command('call pymode#lint#Parse({0})'.format(buf.number))

# pymode:lint_ignore=W0622
