"""PEP257 support."""

from pep257 import PEP257Checker

from pylama.lint import Linter as Abstract


class Linter(Abstract):

    """Check PEP257 errors."""

    @staticmethod
    def run(path, code=None, **meta):
        """PEP257 code checking.

        :return list: List of errors.
        """
        return [
            {'lnum': e.line, 'text': e.message, 'type': 'D'}
            for e in PEP257Checker().check_source(code, path)
        ]
