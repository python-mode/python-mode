""" Check Pyflakes. """

from .. import Linter as BaseLinter


class Linter(BaseLinter):

    """ Pyflakes code check. """

    @staticmethod
    def run(path, code=None, **meta):
        """ Pyflake code checking.

        :return list: List of errors.

        """
        import _ast
        from .pyflakes import checker

        errors = []
        tree = compile(code, path, "exec", _ast.PyCF_ONLY_AST)
        w = checker.Checker(tree, path)
        w.messages = sorted(w.messages, key=lambda m: m.lineno)
        for w in w.messages:
            errors.append(dict(
                lnum=w.lineno,
                text=w.message % w.message_args,
            ))
        return errors
