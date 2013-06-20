""" Interfaces for code checking.
"""
from __future__ import absolute_import, with_statement

import _ast
from os import path as op, environ

from .checkers.pep8 import BaseReport, StyleGuide


__all__ = 'pep8', 'pep257', 'mccabe', 'pyflakes', 'pylint'

PYLINT_RC = op.abspath(op.join(op.dirname(__file__), 'pylint.rc'))


class _PEP8Report(BaseReport):

    def __init__(self, *args, **kwargs):
        super(_PEP8Report, self).__init__(*args, **kwargs)
        self.errors = []

    def init_file(self, filename, lines, expected, line_offset):
        """ Prepare storage for errors. """
        super(_PEP8Report, self).init_file(
            filename, lines, expected, line_offset)
        self.errors = []

    def error(self, line_number, offset, text, check):
        """ Save errors. """
        code = super(_PEP8Report, self).error(
            line_number, offset, text, check)

        self.errors.append(dict(
            text=text,
            type=code,
            col=offset + 1,
            lnum=line_number,
        ))

    def get_file_results(self):
        """ Get errors.

        :return list: List of errors.

        """
        return self.errors


def pep8(path, **meta):
    """ PEP8 code checking.

    :return list: List of errors.

    """
    P8Style = StyleGuide(reporter=_PEP8Report)
    return P8Style.input_file(path)


def mccabe(path, code=None, complexity=8, **meta):
    """ MCCabe code checking.

    :return list: List of errors.

    """
    from .checkers.mccabe import get_code_complexity

    return get_code_complexity(code, complexity, filename=path) or []


def pyflakes(path, code=None, **meta):
    """ Pyflake code checking.

    :return list: List of errors.

    """
    from .checkers.pyflakes import checker

    errors = []
    tree = compile(code, path, "exec", _ast.PyCF_ONLY_AST)
    w = checker.Checker(tree, path)
    w.messages = sorted(w.messages, key=lambda m: m.lineno)
    for w in w.messages:
        errors.append(dict(
            lnum=w.lineno,
            text=w.message % w.message_args,
        ))
    return errors


def pylint(path, **meta):
    """ Pylint code checking.

    :return list: List of errors.

    """
    from sys import version_info
    if version_info > (3, 0):
        import logging
        logging.warn("Pylint don't supported python3 and will be disabled.")
        return []

    from .checkers.pylint.lint import Run
    from .checkers.pylint.reporters import BaseReporter
    from .checkers.pylint.logilab.astng import MANAGER

    MANAGER.astng_cache.clear()

    class Reporter(BaseReporter):

        def __init__(self):
            self.errors = []
            BaseReporter.__init__(self)

        def _display(self, layout):
            pass

        def add_message(self, msg_id, location, msg):
            _, _, line, col = location[1:]
            self.errors.append(dict(
                lnum=line,
                col=col,
                text="%s %s" % (msg_id, msg),
                type=msg_id[0]
            ))

    pylintrc = op.join(environ.get('HOME', ''), '.pylintrc')
    defattrs = '-r n'
    if not op.exists(pylintrc):
        defattrs += ' --rcfile={0}'.format(PYLINT_RC)
    attrs = meta.get('pylint', defattrs.split())

    runner = Run(
        [path] + attrs, reporter=Reporter(), exit=False)
    return runner.linter.reporter.errors


def pep257(path, **meta):
    """ PEP257 code checking.

    :return list: List of errors.

    """
    f = open(path)
    from .checkers.pep257 import check_source

    errors = []
    for er in check_source(f.read(), path):
        errors.append(dict(
            lnum=er.line,
            col=er.char,
            text='C0110 %s' % er.explanation.split('\n')[0].strip(),
            type='W',
        ))
    return errors


# pymode:lint_ignore=W0231
