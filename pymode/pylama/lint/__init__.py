""" Custom module loader. """


class Linter(object): # noqa

    """ Abstract class for linter plugin. """

    @staticmethod
    def allow(path):
        """ Check path is relevant for linter.

        :return bool:

        """

        return path.endswith('.py')

    @staticmethod
    def run(path, **meta):
        """ Method 'run' should be defined. """

        raise NotImplementedError(__doc__)


LINTERS = dict()

from .pylama_mccabe import Linter as MccabeLinter
from .pylama_pep8 import Linter as Pep8Linter
from .pylama_pep257 import Linter as Pep257Linter
from .pylama_pyflakes import Linter as PyflakesLinter
from .pylama_pylint import Linter as PylintLinter

LINTERS['mccabe'] = MccabeLinter()
LINTERS['pep8'] = Pep8Linter()
LINTERS['pep257'] = Pep257Linter()
LINTERS['pyflakes'] = PyflakesLinter()
LINTERS['pylint'] = PylintLinter()
