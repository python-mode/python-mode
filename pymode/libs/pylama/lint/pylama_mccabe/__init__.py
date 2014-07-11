""" Check complexity. """

from .. import Linter as BaseLinter


class Linter(BaseLinter):

    """ Mccabe code complexity. """

    @staticmethod
    def run(path, code=None, params=None, **meta):
        """ MCCabe code checking.

        :return list: List of errors.

        """
        from .mccabe import get_code_complexity

        complexity = int(params.get('complexity', 10))
        return get_code_complexity(code, complexity, filename=path) or []
