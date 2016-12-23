# copyright 2003-2014 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
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
from textwrap import dedent
import unittest

from astroid import nodes
from astroid.node_classes import Assign, Expr, YieldFrom, Name, Const
from astroid.builder import AstroidBuilder
from astroid.scoped_nodes import ClassDef, FunctionDef
from astroid.test_utils import require_version, extract_node


class Python3TC(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.builder = AstroidBuilder()

    @require_version('3.0')
    def test_starred_notation(self):
        astroid = self.builder.string_build("*a, b = [1, 2, 3]", 'test', 'test')

        # Get the star node
        node = next(next(next(astroid.get_children()).get_children()).get_children())

        self.assertTrue(isinstance(node.assign_type(), Assign))

    @require_version('3.3')
    def test_yield_from(self):
        body = dedent("""
        def func():
            yield from iter([1, 2])
        """)
        astroid = self.builder.string_build(body)
        func = astroid.body[0]
        self.assertIsInstance(func, FunctionDef)
        yieldfrom_stmt = func.body[0]

        self.assertIsInstance(yieldfrom_stmt, Expr)
        self.assertIsInstance(yieldfrom_stmt.value, YieldFrom)
        self.assertEqual(yieldfrom_stmt.as_string(),
                         'yield from iter([1, 2])')

    @require_version('3.3')
    def test_yield_from_is_generator(self):
        body = dedent("""
        def func():
            yield from iter([1, 2])
        """)
        astroid = self.builder.string_build(body)
        func = astroid.body[0]
        self.assertIsInstance(func, FunctionDef)
        self.assertTrue(func.is_generator())

    @require_version('3.3')
    def test_yield_from_as_string(self):
        body = dedent("""
        def func():
            yield from iter([1, 2])
            value = yield from other()
        """)
        astroid = self.builder.string_build(body)
        func = astroid.body[0]
        self.assertEqual(func.as_string().strip(), body.strip())

    # metaclass tests

    @require_version('3.0')
    def test_simple_metaclass(self):
        astroid = self.builder.string_build("class Test(metaclass=type): pass")
        klass = astroid.body[0]

        metaclass = klass.metaclass()
        self.assertIsInstance(metaclass, ClassDef)
        self.assertEqual(metaclass.name, 'type')

    @require_version('3.0')
    def test_metaclass_error(self):
        astroid = self.builder.string_build("class Test(metaclass=typ): pass")
        klass = astroid.body[0]
        self.assertFalse(klass.metaclass())

    @require_version('3.0')
    def test_metaclass_imported(self):
        astroid = self.builder.string_build(dedent("""
        from abc import ABCMeta 
        class Test(metaclass=ABCMeta): pass"""))
        klass = astroid.body[1]

        metaclass = klass.metaclass()
        self.assertIsInstance(metaclass, ClassDef)
        self.assertEqual(metaclass.name, 'ABCMeta')

    @require_version('3.0')
    def test_as_string(self):
        body = dedent("""
        from abc import ABCMeta 
        class Test(metaclass=ABCMeta): pass""")
        astroid = self.builder.string_build(body)
        klass = astroid.body[1]

        self.assertEqual(klass.as_string(),
                         '\n\nclass Test(metaclass=ABCMeta):\n    pass\n')

    @require_version('3.0')
    def test_old_syntax_works(self):
        astroid = self.builder.string_build(dedent("""
        class Test:
            __metaclass__ = type
        class SubTest(Test): pass
        """))
        klass = astroid['SubTest']
        metaclass = klass.metaclass()
        self.assertIsNone(metaclass)

    @require_version('3.0')
    def test_metaclass_yes_leak(self):
        astroid = self.builder.string_build(dedent("""
        # notice `ab` instead of `abc`
        from ab import ABCMeta

        class Meta(metaclass=ABCMeta): pass
        """))
        klass = astroid['Meta']
        self.assertIsNone(klass.metaclass())

    @require_version('3.0')
    def test_parent_metaclass(self):
        astroid = self.builder.string_build(dedent("""
        from abc import ABCMeta
        class Test(metaclass=ABCMeta): pass
        class SubTest(Test): pass
        """))
        klass = astroid['SubTest']
        self.assertTrue(klass.newstyle)
        metaclass = klass.metaclass()
        self.assertIsInstance(metaclass, ClassDef)
        self.assertEqual(metaclass.name, 'ABCMeta')

    @require_version('3.0')
    def test_metaclass_ancestors(self):
        astroid = self.builder.string_build(dedent("""
        from abc import ABCMeta

        class FirstMeta(metaclass=ABCMeta): pass
        class SecondMeta(metaclass=type):
            pass

        class Simple:
            pass

        class FirstImpl(FirstMeta): pass
        class SecondImpl(FirstImpl): pass
        class ThirdImpl(Simple, SecondMeta):
            pass
        """))
        classes = {
            'ABCMeta': ('FirstImpl', 'SecondImpl'),
            'type': ('ThirdImpl', )
        }
        for metaclass, names in classes.items():
            for name in names:
                impl = astroid[name]
                meta = impl.metaclass()
                self.assertIsInstance(meta, ClassDef)
                self.assertEqual(meta.name, metaclass)

    @require_version('3.0')
    def test_annotation_support(self):
        astroid = self.builder.string_build(dedent("""
        def test(a: int, b: str, c: None, d, e,
                 *args: float, **kwargs: int)->int:
            pass
        """))
        func = astroid['test']
        self.assertIsInstance(func.args.varargannotation, Name)
        self.assertEqual(func.args.varargannotation.name, 'float')
        self.assertIsInstance(func.args.kwargannotation, Name)
        self.assertEqual(func.args.kwargannotation.name, 'int')
        self.assertIsInstance(func.returns, Name)
        self.assertEqual(func.returns.name, 'int')
        arguments = func.args
        self.assertIsInstance(arguments.annotations[0], Name)
        self.assertEqual(arguments.annotations[0].name, 'int')
        self.assertIsInstance(arguments.annotations[1], Name)
        self.assertEqual(arguments.annotations[1].name, 'str')
        self.assertIsInstance(arguments.annotations[2], Const)
        self.assertIsNone(arguments.annotations[2].value)
        self.assertIsNone(arguments.annotations[3])
        self.assertIsNone(arguments.annotations[4])

        astroid = self.builder.string_build(dedent("""
        def test(a: int=1, b: str=2):
            pass
        """))
        func = astroid['test']
        self.assertIsInstance(func.args.annotations[0], Name)
        self.assertEqual(func.args.annotations[0].name, 'int')
        self.assertIsInstance(func.args.annotations[1], Name)
        self.assertEqual(func.args.annotations[1].name, 'str')
        self.assertIsNone(func.returns)

    @require_version('3.0')
    def test_annotation_as_string(self):
        code1 = dedent('''
        def test(a, b:int=4, c=2, f:'lala'=4)->2:
            pass''')
        code2 = dedent('''
        def test(a:typing.Generic[T], c:typing.Any=24)->typing.Iterable:
            pass''')
        for code in (code1, code2):
            func = extract_node(code)
            self.assertEqual(func.as_string(), code)

    @require_version('3.5')
    def test_unpacking_in_dicts(self):
        code = "{'x': 1, **{'y': 2}}"
        node = extract_node(code)
        self.assertEqual(node.as_string(), code)
        keys = [key for (key, _) in node.items]
        self.assertIsInstance(keys[0], nodes.Const)
        self.assertIsInstance(keys[1], nodes.DictUnpack)

    @require_version('3.5')
    def test_nested_unpacking_in_dicts(self):
        code = "{'x': 1, **{'y': 2, **{'z': 3}}}"
        node = extract_node(code)
        self.assertEqual(node.as_string(), code)

    @require_version('3.5')
    def test_unpacking_in_dict_getitem(self):
        node = extract_node('{1:2, **{2:3, 3:4}, **{5: 6}}')
        for key, expected in ((1, 2), (2, 3), (3, 4), (5, 6)):
            value = node.getitem(key)
            self.assertIsInstance(value, nodes.Const)
            self.assertEqual(value.value, expected)


if __name__ == '__main__':
    unittest.main()
