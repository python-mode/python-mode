""" Check PEP8. """
from .. import Linter as BaseLinter
from .pep8 import BaseReport, StyleGuide


class Linter(BaseLinter):

    """ PEP8 code check. """

    @staticmethod
    def run(path, **meta):
        """ PEP8 code checking.

        :return list: List of errors.

        """
        P8Style = StyleGuide(reporter=_PEP8Report)
        return P8Style.input_file(path)


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
