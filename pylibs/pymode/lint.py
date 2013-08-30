""" Pylama support. """
from __future__ import absolute_import

import json
import locale

from os import path as op
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
    rootpath = interface.eval_code('getcwd()')

    async = int(interface.get_option('lint_async'))
    linters = interface.get_option('lint_checker')
    ignore = interface.get_option('lint_ignore')
    select = interface.get_option('lint_select')
    complexity = interface.get_option('lint_mccabe_complexity') or '0'

    options = parse_options(
        ignore=ignore, select=select, complexity=complexity, linters=linters)

    if async:
        add_task(
            run_checkers, callback=parse_result, title='Code checking',
            buf=buf, options=options, rootpath=rootpath,
        )

    else:
        result = run_checkers(buf=buf, options=options, rootpath=rootpath)
        parse_result(result, buf=buf)


def run_checkers(callback=None, buf=None, options=None, rootpath=None):
    """ Run pylama code.

    :return list: errors

    """
    pylint_options = '--rcfile={0} -r n'.format(
        interface.get_var('lint_config')).split()

    path = buf.name
    if rootpath:
        path = op.relpath(path, rootpath)
    return check_path(path, options=options, pylint=pylint_options)


def parse_result(result, buf=None, **kwargs):
    """ Parse results. """
    interface.command('let g:qf_list = ' + json.dumps(result))
    interface.command('call pymode#lint#Parse({0})'.format(buf.number))

# pymode:lint_ignore=W0622
