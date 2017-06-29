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

import collections
import warnings


class TransformVisitor(object):
    """A visitor for handling transforms.

    The standard approach of using it is to call
    :meth:`~visit` with an *astroid* module and the class
    will take care of the rest, walking the tree and running the
    transforms for each encountered node.
    """

    def __init__(self):
        self.transforms = collections.defaultdict(list)

    def _transform(self, node):
        """Call matching transforms for the given node if any and return the
        transformed node.
        """
        cls = node.__class__
        if cls not in self.transforms:
            # no transform registered for this class of node
            return node

        transforms = self.transforms[cls]
        orig_node = node  # copy the reference
        for transform_func, predicate in transforms:
            if predicate is None or predicate(node):
                ret = transform_func(node)
                # if the transformation function returns something, it's
                # expected to be a replacement for the node
                if ret is not None:
                    if node is not orig_node:
                        # node has already be modified by some previous
                        # transformation, warn about it
                        warnings.warn('node %s substituted multiple times' % node)
                    node = ret
        return node

    def _visit(self, node):
        if hasattr(node, '_astroid_fields'):
            for field in node._astroid_fields:
                value = getattr(node, field)
                visited = self._visit_generic(value)
                setattr(node, field, visited)
        return self._transform(node)

    def _visit_generic(self, node):
        if isinstance(node, list):
            return [self._visit_generic(child) for child in node]
        elif isinstance(node, tuple):
            return tuple(self._visit_generic(child) for child in node)
        else:
            return self._visit(node)

    def register_transform(self, node_class, transform, predicate=None):
        """Register `transform(node)` function to be applied on the given
        astroid's `node_class` if `predicate` is None or returns true
        when called with the node as argument.

        The transform function may return a value which is then used to
        substitute the original node in the tree.
        """
        self.transforms[node_class].append((transform, predicate))

    def unregister_transform(self, node_class, transform, predicate=None):
        """Unregister the given transform."""
        self.transforms[node_class].remove((transform, predicate))

    def visit(self, module):
        """Walk the given astroid *tree* and transform each encountered node

        Only the nodes which have transforms registered will actually
        be replaced or changed.
        """
        module.body = [self._visit(child) for child in module.body]
        return self._transform(module)
