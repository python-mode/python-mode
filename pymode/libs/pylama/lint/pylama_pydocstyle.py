"""pydocstyle support."""

THIRD_ARG = True
try:
    #: Import for pydocstyle 2.0.0 and newer
    from pydocstyle import ConventionChecker as PyDocChecker
except ImportError:
    #: Backward compatibility for pydocstyle prior to 2.0.0
    from pydocstyle import PEP257Checker as PyDocChecker
    THIRD_ARG = False

from pylama.lint import Linter as Abstract


class Linter(Abstract):

    """Check pydocstyle errors."""

    @staticmethod
    def run(path, code=None, **meta):
        """pydocstyle code checking.

        :return list: List of errors.
        """
        check_source_args = (code, path, None) if THIRD_ARG else (code, path)
        return [{
            'lnum': e.line,
            # Remove colon after error code ("D403: ..." => "D403 ...").
            'text': (e.message[0:4] + e.message[5:]
                     if e.message[4] == ':' else e.message),
            'type': 'D',
            'number': e.code
        } for e in PyDocChecker().check_source(*check_source_args)]
