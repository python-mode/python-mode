"""Pyflakes support."""

from pyflakes import checker

from pylama.lint import Linter as Abstract


checker.messages.UnusedImport.message = "W0611 %r imported but unused"
checker.messages.RedefinedWhileUnused.message = "W0404 redefinition of unused %r from line %r"
checker.messages.RedefinedInListComp.message = "W0621 list comprehension redefines %r from line %r"
checker.messages.ImportShadowedByLoopVar.message = "W0621 import %r from line %r shadowed by loop variable"
checker.messages.ImportStarUsed.message = "W0401 'from %s import *' used; unable to detect undefined names"
checker.messages.UndefinedName.message = "E0602 undefined name %r"
checker.messages.DoctestSyntaxError.message = "W0511 syntax error in doctest"
checker.messages.UndefinedExport.message = "E0603 undefined name %r in __all__"
checker.messages.UndefinedLocal.message = "E0602 local variable %r (defined in enclosing scope on line %r) referenced before assignment"
checker.messages.DuplicateArgument.message = "E1122 duplicate argument %r in function definition"
checker.messages.LateFutureImport.message = "W0410 future import(s) %r after other statements"
checker.messages.UnusedVariable.message = "W0612 local variable %r is assigned to but never used"
checker.messages.ReturnWithArgsInsideGenerator.message = "E0106 'return' with argument inside generator"
checker.messages.ReturnOutsideFunction.message = "E0104 'return' outside function"


class Linter(Abstract):

    """Pyflakes runner."""

    @staticmethod
    def run(path, code=None, params=None, **meta):
        """Check code with pyflakes.

        :return list: List of errors.
        """
        import _ast

        builtins = params.get("builtins", "")

        if builtins:
            builtins = builtins.split(",")

        tree = compile(code, path, "exec", _ast.PyCF_ONLY_AST)
        w = checker.Checker(tree, path, builtins=builtins)
        w.messages = sorted(w.messages, key=lambda m: m.lineno)
        return [
            {'lnum': m.lineno, 'text': m.message % m.message_args}
            for m in sorted(w.messages, key=lambda m: m.lineno)
        ]

#  pylama:ignore=E501,C0301
