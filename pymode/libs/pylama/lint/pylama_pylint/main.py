""" Pylint support. """
from os import path as op, environ

from pylama.lint import Linter as BaseLinter # noqa

from astroid import MANAGER  # noqa
from pylint.lint import Run  # noqa
from pylint.reporters import BaseReporter  # noqa


PYLINT_RC = op.abspath(op.join(op.dirname(__file__), 'pylint.rc'))


class Linter(BaseLinter):

    """ Check code with pylint. """

    @staticmethod
    def run(path, **meta): # noqa
        """ Pylint code checking.

        :return list: List of errors.

        """

        MANAGER.astroid_cache.clear()

        class Reporter(BaseReporter):

            def __init__(self):
                self.errors = []
                super(Reporter, self).__init__()

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
