""" Check PEP257. """

from .. import Linter as BaseLinter


class Linter(BaseLinter):

    """ Mccabe code complexity. """

    @staticmethod
    def run(path, code=None, **meta):
        """ PEP257 code checking.

        :return list: List of errors.

        """
        from .pep257 import PEP257Checker

        errors = []
        for er in PEP257Checker().check_source(code, path):
            errors.append(dict(
                lnum=er.line,
                text=er.message,
                type='D',
            ))
        return errors
