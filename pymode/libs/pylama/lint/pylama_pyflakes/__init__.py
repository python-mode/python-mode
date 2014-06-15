""" Check Pyflakes. """
import sys
from os import path as op

from .. import Linter as BaseLinter


# Use local version of pyflakes
path = op.dirname(op.abspath(__file__))
sys.path.insert(0, path)

from pyflakes import checker


class Linter(BaseLinter):

    """ Pyflakes code check. """

    def __init__(self):
        if checker.messages.UndefinedName.message != "E0602 undefined name %r":
            monkey_patch_messages(checker.messages)

    @staticmethod
    def run(path, code=None, params=None, **meta):
        """ Pyflake code checking.

        :return list: List of errors.

        """
        import _ast

        builtins = params.get("builtins", "")

        if builtins:
            builtins = builtins.split(",")

        errors = []
        tree = compile(code, path, "exec", _ast.PyCF_ONLY_AST)
        w = checker.Checker(tree, path, builtins=builtins)
        w.messages = sorted(w.messages, key=lambda m: m.lineno)
        for w in w.messages:
            errors.append(dict(
                lnum=w.lineno,
                text=w.message % w.message_args,
            ))
        return errors


def monkey_patch_messages(messages):
    """ Patch pyflakes messages. """

    messages.LateFutureImport.message = "W0410 future import(s) %r after other statements"
    messages.ImportStarUsed.message = "W0401 'from %s import *' used; unable to detect undefined names"
    messages.RedefinedWhileUnused.message = "W0404 redefinition of unused %r from line %r"
    messages.DoctestSyntaxError.message = "W0511 syntax error in doctest"
    messages.UnusedImport.message = "W0611 %r imported but unused"
    messages.UnusedVariable.message = "W0612 local variable %r is assigned to but never used"
    messages.RedefinedInListComp.message = "W0621 list comprehension redefines %r from line %r"
    messages.Redefined.message = "W0621 redefinition of %r from line %r"
    messages.ImportShadowedByLoopVar.message = "W0621 import %r from line %r shadowed by loop variable"
    messages.ReturnWithArgsInsideGenerator.message = "E0106 'return' with argument inside generator"
    messages.UndefinedName.message = "E0602 undefined name %r"
    messages.UndefinedLocal.message = "E0602 local variable %r (defined in enclosing scope on line %r) referenced before assignment"
    messages.UndefinedExport.message = "E0603 undefined name %r in __all__"
    messages.DuplicateArgument.message = "E1122 duplicate argument %r in function definition"
