"""Code complexity checking."""
from mccabe import McCabeChecker

from pylama.lint import Linter as Abstract
import ast


class Linter(Abstract):

    """Run complexity checking."""

    @staticmethod
    def run(path, code=None, params=None, **meta):
        """MCCabe code checking.

        :return list: List of errors.
        """
        try:
            tree = compile(code, path, "exec", ast.PyCF_ONLY_AST)
        except SyntaxError as exc:
            return [{'lnum': exc.lineno, 'text': 'Invalid syntax: %s' % exc.text.strip()}]

        McCabeChecker.max_complexity = int(params.get('complexity', 10))
        return [
            {'lnum': lineno, 'offset': offset, 'text': text, 'type': McCabeChecker._code}
            for lineno, offset, text, _ in McCabeChecker(tree, path).run()
        ]

#  pylama:ignore=W0212
