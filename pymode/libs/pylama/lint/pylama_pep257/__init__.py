""" Check PEP257. """

from .. import Linter as BaseLinter


class Linter(BaseLinter):

    """ Mccabe code complexity. """

    @staticmethod
    def run(path, code=None, **meta):
        """ PEP257 code checking.

        :return list: List of errors.

        """
        from .pep257 import check_source

        errors = []
        for er in check_source(code, path):
            errors.append(dict(
                lnum=er.line,
                col=er.char,
                text='C0110 %s' % er.explanation.split('\n')[0].strip(),
                type='W',
            ))
        return errors
