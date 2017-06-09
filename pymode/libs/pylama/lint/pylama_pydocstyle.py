"""pydocstyle support."""

from pydocstyle import PEP257Checker

from pylama.lint import Linter as Abstract


class Linter(Abstract):

    """Check pydocstyle errors."""

    @staticmethod
    def run(path, code=None, **meta):
        """pydocstyle code checking.

        :return list: List of errors.
        """
        return [{
            'lnum': e.line,
            # Remove colon after error code ("D403: ..." => "D403 ...").
            'text': (e.message[0:4] + e.message[5:]
                     if e.message[4] == ':' else e.message),
            'type': 'D',
            'number': e.code
        } for e in PEP257Checker().check_source(code, path)]
