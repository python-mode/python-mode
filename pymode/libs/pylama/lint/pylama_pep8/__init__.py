""" Check PEP8. """
from .. import Linter as BaseLinter
from .pep8 import BaseReport, StyleGuide

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


class Linter(BaseLinter):

    """ PEP8 code check. """

    @staticmethod
    def run(path, code=None, params=None, **meta):
        """ PEP8 code checking.

        :return list: List of errors.

        """
        P8Style = StyleGuide(reporter=_PEP8Report, **params)
        buf = StringIO(code)
        return P8Style.input_file(path, lines=buf.readlines())


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

        if code:
            self.errors.append(dict(
                text=text,
                type=code.replace('E', 'C'),
                col=offset + 1,
                lnum=line_number,
            ))

    def get_file_results(self):
        """ Get errors.

        :return list: List of errors.

        """
        return self.errors
