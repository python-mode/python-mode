# copyright 2003-2015 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
# contact http://www.logilab.fr/ -- mailto:contact@logilab.fr
#
# This file is part of astroid.
#
# astroid is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation, either version 2.1 of the License, or (at your
# option) any later version.
#
# astroid is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
# for more details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with astroid. If not, see <http://www.gnu.org/licenses/>.
"""Small AST optimizations."""

import _ast

from astroid import nodes


__all__ = ('ASTPeepholeOptimizer', )


try:
    _TYPES = (_ast.Str, _ast.Bytes)
except AttributeError:
    _TYPES = (_ast.Str, )


class ASTPeepholeOptimizer(object):
    """Class for applying small optimizations to generate new AST."""

    def optimize_binop(self, node):
        """Optimize BinOps with string Const nodes on the lhs.

        This fixes an infinite recursion crash, where multiple
        strings are joined using the addition operator. With a
        sufficient number of such strings, astroid will fail
        with a maximum recursion limit exceeded. The
        function will return a Const node with all the strings
        already joined.
        Return ``None`` if no AST node can be obtained
        through optimization.
        """
        ast_nodes = []
        current = node
        while isinstance(current, _ast.BinOp):
            # lhs must be a BinOp with the addition operand.
            if not isinstance(current.left, _ast.BinOp):
                return
            if (not isinstance(current.left.op, _ast.Add)
                    or not isinstance(current.op, _ast.Add)):
                return

            # rhs must a str / bytes.
            if not isinstance(current.right, _TYPES):
                return

            ast_nodes.append(current.right.s)
            current = current.left

            if (isinstance(current, _ast.BinOp)
                    and isinstance(current.left, _TYPES)
                    and isinstance(current.right, _TYPES)):
                # Stop early if we are at the last BinOp in
                # the operation
                ast_nodes.append(current.right.s)
                ast_nodes.append(current.left.s)
                break

        if not ast_nodes:
            return

        # If we have inconsistent types, bail out.
        known = type(ast_nodes[0])
        if any(type(element) is not known
               for element in ast_nodes[1:]):
            return

        value = known().join(reversed(ast_nodes))
        newnode = nodes.Const(value)
        return newnode
