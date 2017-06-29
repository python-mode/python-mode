from radon.visitors import ComplexityVisitor
from radon.complexity import add_inner_blocks

from pylama.lint import Linter as Abstract


class Linter(Abstract):

    """Radon runner."""

    @staticmethod
    def run(path, code=None, params=None, ignore=None, select=None, **meta):
        """Check code with Radon.

        :return list: List of errors.
        """
        complexity = params.get('complexity', 10)
        no_assert = params.get('no_assert', False)
        show_closures = params.get('show_closures', False)

        visitor = ComplexityVisitor.from_code(code, no_assert=no_assert)
        blocks = visitor.blocks
        if show_closures:
            blocks = add_inner_blocks(blocks)

        return [
            {'lnum': block.lineno, 'col': block.col_offset, 'type': 'R', 'number': 'R709',
             'text': 'R701: %s is too complex %d' % (block.name, block.complexity)}
            for block in visitor.blocks if block.complexity > complexity
        ]

