""" Check PEP257. """

from .. import Linter as BaseLinter


class Linter(BaseLinter):

    """ Mccabe code complexity. """

    @staticmethod
    def run(path, **meta):
        """ PEP257 code checking.

        :return list: List of errors.

        """
        f = open(path)
        from .pep257 import check_source

        errors = []
        for er in check_source(f.read(), path):
            errors.append(dict(
                lnum=er.line,
                col=er.char,
                text='C0110 %s' % er.explanation.split('\n')[0].strip(),
                type='W',
            ))
        return errors
