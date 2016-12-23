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

import contextlib
import unittest

import astroid
from astroid.test_utils import extract_node, require_version
from astroid import InferenceError
from astroid import nodes
from astroid import util
from astroid.node_classes import AssignName, Const, Name, Starred


@contextlib.contextmanager
def _add_transform(manager, node, transform, predicate=None):
    manager.register_transform(node, transform, predicate)
    try:
        yield
    finally:
        manager.unregister_transform(node, transform, predicate)


class ProtocolTests(unittest.TestCase):

    def assertConstNodesEqual(self, nodes_list_expected, nodes_list_got):
        self.assertEqual(len(nodes_list_expected), len(nodes_list_got))
        for node in nodes_list_got:
            self.assertIsInstance(node, Const)
        for node, expected_value in zip(nodes_list_got, nodes_list_expected):
            self.assertEqual(expected_value, node.value)

    def assertNameNodesEqual(self, nodes_list_expected, nodes_list_got):
        self.assertEqual(len(nodes_list_expected), len(nodes_list_got))
        for node in nodes_list_got:
            self.assertIsInstance(node, Name)
        for node, expected_name in zip(nodes_list_got, nodes_list_expected):
            self.assertEqual(expected_name, node.name)

    def test_assigned_stmts_simple_for(self):
        assign_stmts = extract_node("""
        for a in (1, 2, 3):  #@
          pass

        for b in range(3): #@
          pass
        """)

        for1_assnode = next(assign_stmts[0].nodes_of_class(AssignName))
        assigned = list(for1_assnode.assigned_stmts())
        self.assertConstNodesEqual([1, 2, 3], assigned)

        for2_assnode = next(assign_stmts[1].nodes_of_class(AssignName))
        self.assertRaises(InferenceError,
                          list, for2_assnode.assigned_stmts())

    @require_version(minver='3.0')
    def test_assigned_stmts_starred_for(self):
        assign_stmts = extract_node("""
        for *a, b in ((1, 2, 3), (4, 5, 6, 7)): #@
            pass
        """)

        for1_starred = next(assign_stmts.nodes_of_class(Starred))
        assigned = next(for1_starred.assigned_stmts())
        self.assertEqual(assigned, util.YES)

    def _get_starred_stmts(self, code):
        assign_stmt = extract_node("{} #@".format(code))
        starred = next(assign_stmt.nodes_of_class(Starred))
        return next(starred.assigned_stmts())

    def _helper_starred_expected_const(self, code, expected):
        stmts = self._get_starred_stmts(code)
        self.assertIsInstance(stmts, nodes.List)
        stmts = stmts.elts
        self.assertConstNodesEqual(expected, stmts)

    def _helper_starred_expected(self, code, expected):
        stmts = self._get_starred_stmts(code)
        self.assertEqual(expected, stmts)

    def _helper_starred_inference_error(self, code):
        assign_stmt = extract_node("{} #@".format(code))
        starred = next(assign_stmt.nodes_of_class(Starred))
        self.assertRaises(InferenceError, list, starred.assigned_stmts())

    @require_version(minver='3.0')
    def test_assigned_stmts_starred_assnames(self):
        self._helper_starred_expected_const(
            "a, *b = (1, 2, 3, 4) #@", [2, 3, 4])
        self._helper_starred_expected_const(
            "*a, b = (1, 2, 3) #@", [1, 2])
        self._helper_starred_expected_const(
            "a, *b, c = (1, 2, 3, 4, 5) #@",
            [2, 3, 4])
        self._helper_starred_expected_const(
            "a, *b = (1, 2) #@", [2])
        self._helper_starred_expected_const(
            "*b, a = (1, 2) #@", [1])
        self._helper_starred_expected_const(
            "[*b] = (1, 2) #@", [1, 2])

    @require_version(minver='3.0')
    def test_assigned_stmts_starred_yes(self):
        # Not something iterable and known
        self._helper_starred_expected("a, *b = range(3) #@", util.YES)
        # Not something inferrable
        self._helper_starred_expected("a, *b = balou() #@", util.YES)
        # In function, unknown.
        self._helper_starred_expected("""
        def test(arg):
            head, *tail = arg #@""", util.YES)
        # These cases aren't worth supporting.
        self._helper_starred_expected(
            "a, (*b, c), d = (1, (2, 3, 4), 5) #@", util.YES)

    @require_version(minver='3.0')
    def test_assign_stmts_starred_fails(self):
        # Too many starred
        self._helper_starred_inference_error("a, *b, *c = (1, 2, 3) #@")
        # Too many lhs values
        self._helper_starred_inference_error("a, *b, c = (1, 2) #@")
        # This could be solved properly, but it complicates needlessly the
        # code for assigned_stmts, without oferring real benefit.
        self._helper_starred_inference_error(
            "(*a, b), (c, *d) = (1, 2, 3), (4, 5, 6) #@")

    def test_assigned_stmts_assignments(self):
        assign_stmts = extract_node("""
        c = a #@

        d, e = b, c #@
        """)

        simple_assnode = next(assign_stmts[0].nodes_of_class(AssignName))
        assigned = list(simple_assnode.assigned_stmts())
        self.assertNameNodesEqual(['a'], assigned)

        assnames = assign_stmts[1].nodes_of_class(AssignName)
        simple_mul_assnode_1 = next(assnames)
        assigned = list(simple_mul_assnode_1.assigned_stmts())
        self.assertNameNodesEqual(['b'], assigned)
        simple_mul_assnode_2 = next(assnames)
        assigned = list(simple_mul_assnode_2.assigned_stmts())
        self.assertNameNodesEqual(['c'], assigned)

    def test_sequence_assigned_stmts_not_accepting_empty_node(self):
        def transform(node):
            node.root().locals['__all__'] = [node.value]

        manager = astroid.MANAGER
        with _add_transform(manager, astroid.Assign, transform):
            module = astroid.parse('''
            __all__ = ['a']
            ''')
            module.wildcard_import_names()


if __name__ == '__main__':
    unittest.main()
