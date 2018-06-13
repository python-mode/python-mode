# Copyright (c) 2013-2014 Google, Inc.
# Copyright (c) 2014-2016 Claudiu Popa <pcmanticore@gmail.com>
# Copyright (c) 2015 Philip Lorenz <philip@bithub.de>
# Copyright (c) 2015 LOGILAB S.A. (Paris, FRANCE) <contact@logilab.fr>
# Copyright (c) 2015 raylu <lurayl@gmail.com>
# Copyright (c) 2015-2016 Cara Vinson <ceridwenv@gmail.com>

# Licensed under the LGPL: https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html
# For details: https://github.com/PyCQA/astroid/blob/master/COPYING.LESSER

"""Tests for basic functionality in astroid.brain."""
import queue

try:
    import multiprocessing # pylint: disable=unused-import
    HAS_MULTIPROCESSING = True
except ImportError:
    HAS_MULTIPROCESSING = False
import sys
import unittest

try:
    import enum # pylint: disable=unused-import
    HAS_ENUM = True
except ImportError:
    try:
        import enum34 as enum # pylint: disable=unused-import
        HAS_ENUM = True
    except ImportError:
        HAS_ENUM = False

try:
    import nose # pylint: disable=unused-import
    HAS_NOSE = True
except ImportError:
    HAS_NOSE = False

try:
    import dateutil # pylint: disable=unused-import
    HAS_DATEUTIL = True
except ImportError:
    HAS_DATEUTIL = False

import pytest
HAS_PYTEST = True

try:
    import attr as attr_module # pylint: disable=unused-import
    HAS_ATTR = True
except ImportError:
    HAS_ATTR = False

from astroid import MANAGER
from astroid import bases
from astroid import builder
from astroid import nodes
from astroid import util
from astroid import test_utils
import astroid


class HashlibTest(unittest.TestCase):
    def _assert_hashlib_class(self, class_obj):
        self.assertIn('update', class_obj)
        self.assertIn('digest', class_obj)
        self.assertIn('hexdigest', class_obj)
        self.assertIn('block_size', class_obj)
        self.assertIn('digest_size', class_obj)
        self.assertEqual(len(class_obj['__init__'].args.args), 2)
        self.assertEqual(len(class_obj['__init__'].args.defaults), 1)
        self.assertEqual(len(class_obj['update'].args.args), 2)
        self.assertEqual(len(class_obj['digest'].args.args), 1)
        self.assertEqual(len(class_obj['hexdigest'].args.args), 1)

    def test_hashlib(self):
        """Tests that brain extensions for hashlib work."""
        hashlib_module = MANAGER.ast_from_module_name('hashlib')
        for class_name in ['md5', 'sha1']:
            class_obj = hashlib_module[class_name]
            self._assert_hashlib_class(class_obj)

    @test_utils.require_version(minver='3.6')
    def test_hashlib_py36(self):
        hashlib_module = MANAGER.ast_from_module_name('hashlib')
        for class_name in ['sha3_224', 'sha3_512', 'shake_128']:
            class_obj = hashlib_module[class_name]
            self._assert_hashlib_class(class_obj)


class CollectionsDequeTests(unittest.TestCase):
    def _inferred_queue_instance(self):
        node = builder.extract_node("""
        import collections
        q = collections.deque([])
        q
        """)
        return next(node.infer())

    def test_deque(self):
        inferred = self._inferred_queue_instance()
        self.assertTrue(inferred.getattr('__len__'))

    @test_utils.require_version(minver='3.5')
    def test_deque_py35methods(self):
        inferred = self._inferred_queue_instance()
        self.assertIn('copy', inferred.locals)
        self.assertIn('insert', inferred.locals)
        self.assertIn('index', inferred.locals)


class OrderedDictTest(unittest.TestCase):
    def _inferred_ordered_dict_instance(self):
        node = builder.extract_node("""
        import collections
        d = collections.OrderedDict()
        d
        """)
        return next(node.infer())

    @test_utils.require_version(minver='3.4')
    def test_ordered_dict_py34method(self):
        inferred = self._inferred_ordered_dict_instance()
        self.assertIn('move_to_end', inferred.locals)


class NamedTupleTest(unittest.TestCase):

    def test_namedtuple_base(self):
        klass = builder.extract_node("""
        from collections import namedtuple

        class X(namedtuple("X", ["a", "b", "c"])):
           pass
        """)
        self.assertEqual(
            [anc.name for anc in klass.ancestors()],
            ['X', 'tuple', 'object'])
        for anc in klass.ancestors():
            self.assertFalse(anc.parent is None)

    def test_namedtuple_inference(self):
        klass = builder.extract_node("""
        from collections import namedtuple

        name = "X"
        fields = ["a", "b", "c"]
        class X(namedtuple(name, fields)):
           pass
        """)
        base = next(base for base in klass.ancestors()
                    if base.name == 'X')
        self.assertSetEqual({"a", "b", "c"}, set(base.instance_attrs))

    def test_namedtuple_inference_failure(self):
        klass = builder.extract_node("""
        from collections import namedtuple

        def foo(fields):
           return __(namedtuple("foo", fields))
        """)
        self.assertIs(util.Uninferable, next(klass.infer()))

    def test_namedtuple_advanced_inference(self):
        # urlparse return an object of class ParseResult, which has a
        # namedtuple call and a mixin as base classes
        result = builder.extract_node("""
        import six

        result = __(six.moves.urllib.parse.urlparse('gopher://'))
        """)
        instance = next(result.infer())
        self.assertGreaterEqual(len(instance.getattr('scheme')), 1)
        self.assertGreaterEqual(len(instance.getattr('port')), 1)
        with self.assertRaises(astroid.AttributeInferenceError):
            instance.getattr('foo')
        self.assertGreaterEqual(len(instance.getattr('geturl')), 1)
        self.assertEqual(instance.name, 'ParseResult')

    def test_namedtuple_instance_attrs(self):
        result = builder.extract_node('''
        from collections import namedtuple
        namedtuple('a', 'a b c')(1, 2, 3) #@
        ''')
        inferred = next(result.infer())
        for name, attr in inferred.instance_attrs.items():
            self.assertEqual(attr[0].attrname, name)

    def test_namedtuple_uninferable_fields(self):
        node = builder.extract_node('''
        x = [A] * 2
        from collections import namedtuple
        l = namedtuple('a', x)
        l(1)
        ''')
        inferred = next(node.infer())
        self.assertIs(util.Uninferable, inferred)

    def test_namedtuple_access_class_fields(self):
        node = builder.extract_node("""
        from collections import namedtuple
        Tuple = namedtuple("Tuple", "field other")
        Tuple #@
        """)
        inferred = next(node.infer())
        self.assertIn('field', inferred.locals)
        self.assertIn('other', inferred.locals)

    def test_namedtuple_rename_keywords(self):
        node = builder.extract_node("""
        from collections import namedtuple
        Tuple = namedtuple("Tuple", "abc def", rename=True)
        Tuple #@
        """)
        inferred = next(node.infer())
        self.assertIn('abc', inferred.locals)
        self.assertIn('_1', inferred.locals)

    def test_namedtuple_rename_duplicates(self):
        node = builder.extract_node("""
        from collections import namedtuple
        Tuple = namedtuple("Tuple", "abc abc abc", rename=True)
        Tuple #@
        """)
        inferred = next(node.infer())
        self.assertIn('abc', inferred.locals)
        self.assertIn('_1', inferred.locals)
        self.assertIn('_2', inferred.locals)

    def test_namedtuple_rename_uninferable(self):
        node = builder.extract_node("""
        from collections import namedtuple
        Tuple = namedtuple("Tuple", "a b c", rename=UNINFERABLE)
        Tuple #@
        """)
        inferred = next(node.infer())
        self.assertIn('a', inferred.locals)
        self.assertIn('b', inferred.locals)
        self.assertIn('c', inferred.locals)

    def test_namedtuple_func_form(self):
        node = builder.extract_node("""
        from collections import namedtuple
        Tuple = namedtuple(typename="Tuple", field_names="a b c", rename=UNINFERABLE)
        Tuple #@
        """)
        inferred = next(node.infer())
        self.assertEqual(inferred.name, 'Tuple')
        self.assertIn('a', inferred.locals)
        self.assertIn('b', inferred.locals)
        self.assertIn('c', inferred.locals)

    def test_namedtuple_func_form_args_and_kwargs(self):
        node = builder.extract_node("""
        from collections import namedtuple
        Tuple = namedtuple("Tuple", field_names="a b c", rename=UNINFERABLE)
        Tuple #@
        """)
        inferred = next(node.infer())
        self.assertEqual(inferred.name, 'Tuple')
        self.assertIn('a', inferred.locals)
        self.assertIn('b', inferred.locals)
        self.assertIn('c', inferred.locals)

    def test_namedtuple_bases_are_actually_names_not_nodes(self):
        node = builder.extract_node("""
        from collections import namedtuple
        Tuple = namedtuple("Tuple", field_names="a b c", rename=UNINFERABLE)
        Tuple #@
        """)
        inferred = next(node.infer())
        self.assertIsInstance(inferred, astroid.ClassDef)
        self.assertIsInstance(inferred.bases[0], astroid.Name)
        self.assertEqual(inferred.bases[0].name, 'tuple')


class DefaultDictTest(unittest.TestCase):

    def test_1(self):
        node = builder.extract_node('''
        from collections import defaultdict

        X = defaultdict(int)
        X[0]
        ''')
        inferred = next(node.infer())
        self.assertIs(util.Uninferable, inferred)


class ModuleExtenderTest(unittest.TestCase):
    def testExtensionModules(self):
        transformer = MANAGER._transform
        for extender, _ in transformer.transforms[nodes.Module]:
            n = nodes.Module('__main__', None)
            extender(n)


@unittest.skipUnless(HAS_NOSE, "This test requires nose library.")
class NoseBrainTest(unittest.TestCase):

    def test_nose_tools(self):
        methods = builder.extract_node("""
        from nose.tools import assert_equal
        from nose.tools import assert_equals
        from nose.tools import assert_true
        assert_equal = assert_equal #@
        assert_true = assert_true #@
        assert_equals = assert_equals #@
        """)
        assert_equal = next(methods[0].value.infer())
        assert_true = next(methods[1].value.infer())
        assert_equals = next(methods[2].value.infer())

        self.assertIsInstance(assert_equal, astroid.BoundMethod)
        self.assertIsInstance(assert_true, astroid.BoundMethod)
        self.assertIsInstance(assert_equals, astroid.BoundMethod)
        self.assertEqual(assert_equal.qname(),
                         'unittest.case.TestCase.assertEqual')
        self.assertEqual(assert_true.qname(),
                         'unittest.case.TestCase.assertTrue')
        self.assertEqual(assert_equals.qname(),
                         'unittest.case.TestCase.assertEqual')


class SixBrainTest(unittest.TestCase):

    def test_attribute_access(self):
        ast_nodes = builder.extract_node('''
        import six
        six.moves.http_client #@
        six.moves.urllib_parse #@
        six.moves.urllib_error #@
        six.moves.urllib.request #@
        ''')
        http_client = next(ast_nodes[0].infer())
        self.assertIsInstance(http_client, nodes.Module)
        self.assertEqual(http_client.name, 'http.client')

        urllib_parse = next(ast_nodes[1].infer())
        self.assertIsInstance(urllib_parse, nodes.Module)
        self.assertEqual(urllib_parse.name, 'urllib.parse')
        urljoin = next(urllib_parse.igetattr('urljoin'))
        urlencode = next(urllib_parse.igetattr('urlencode'))
        self.assertIsInstance(urljoin, nodes.FunctionDef)
        self.assertEqual(urljoin.qname(), 'urllib.parse.urljoin')
        self.assertIsInstance(urlencode, nodes.FunctionDef)
        self.assertEqual(urlencode.qname(), 'urllib.parse.urlencode')

        urllib_error = next(ast_nodes[2].infer())
        self.assertIsInstance(urllib_error, nodes.Module)
        self.assertEqual(urllib_error.name, 'urllib.error')
        urlerror = next(urllib_error.igetattr('URLError'))
        self.assertIsInstance(urlerror, nodes.ClassDef)
        content_too_short = next(urllib_error.igetattr('ContentTooShortError'))
        self.assertIsInstance(content_too_short, nodes.ClassDef)

        urllib_request = next(ast_nodes[3].infer())
        self.assertIsInstance(urllib_request, nodes.Module)
        self.assertEqual(urllib_request.name, 'urllib.request')
        urlopen = next(urllib_request.igetattr('urlopen'))
        urlretrieve = next(urllib_request.igetattr('urlretrieve'))
        self.assertIsInstance(urlopen, nodes.FunctionDef)
        self.assertEqual(urlopen.qname(), 'urllib.request.urlopen')
        self.assertIsInstance(urlretrieve, nodes.FunctionDef)
        self.assertEqual(urlretrieve.qname(), 'urllib.request.urlretrieve')

    def test_from_imports(self):
        ast_node = builder.extract_node('''
        from six.moves import http_client
        http_client.HTTPSConnection #@
        ''')
        inferred = next(ast_node.infer())
        self.assertIsInstance(inferred, nodes.ClassDef)
        qname = 'http.client.HTTPSConnection'
        self.assertEqual(inferred.qname(), qname)

    def test_from_submodule_imports(self):
        """Make sure ulrlib submodules can be imported from

        See PyCQA/pylint#1640 for relevant issue
        """
        ast_node = builder.extract_node('''
        from six.moves.urllib.parse import urlparse
        urlparse #@
        ''')
        inferred = next(ast_node.infer())
        self.assertIsInstance(inferred, nodes.FunctionDef)


@unittest.skipUnless(HAS_MULTIPROCESSING,
                     'multiprocesing is required for this test, but '
                     'on some platforms it is missing '
                     '(Jython for instance)')
class MultiprocessingBrainTest(unittest.TestCase):

    def test_multiprocessing_module_attributes(self):
        # Test that module attributes are working,
        # especially on Python 3.4+, where they are obtained
        # from a context.
        module = builder.extract_node("""
        import multiprocessing
        """)
        module = module.do_import_module('multiprocessing')
        cpu_count = next(module.igetattr('cpu_count'))
        if sys.version_info < (3, 4):
            self.assertIsInstance(cpu_count, nodes.FunctionDef)
        else:
            self.assertIsInstance(cpu_count, astroid.BoundMethod)

    def test_module_name(self):
        module = builder.extract_node("""
        import multiprocessing
        multiprocessing.SyncManager()
        """)
        inferred_sync_mgr = next(module.infer())
        module = inferred_sync_mgr.root()
        self.assertEqual(module.name, 'multiprocessing.managers')

    def test_multiprocessing_manager(self):
        # Test that we have the proper attributes
        # for a multiprocessing.managers.SyncManager
        module = builder.parse("""
        import multiprocessing
        manager = multiprocessing.Manager()
        queue = manager.Queue()
        joinable_queue = manager.JoinableQueue()
        event = manager.Event()
        rlock = manager.RLock()
        bounded_semaphore = manager.BoundedSemaphore()
        condition = manager.Condition()
        barrier = manager.Barrier()
        pool = manager.Pool()
        list = manager.list()
        dict = manager.dict()
        value = manager.Value()
        array = manager.Array()
        namespace = manager.Namespace()
        """)
        ast_queue = next(module['queue'].infer())
        self.assertEqual(ast_queue.qname(), "{}.Queue".format(queue.__name__))

        joinable_queue = next(module['joinable_queue'].infer())
        self.assertEqual(joinable_queue.qname(),
                         "{}.Queue".format(queue.__name__))

        event = next(module['event'].infer())
        event_name = "threading.Event"
        self.assertEqual(event.qname(), event_name)

        rlock = next(module['rlock'].infer())
        rlock_name = "threading._RLock"
        self.assertEqual(rlock.qname(), rlock_name)

        bounded_semaphore = next(module['bounded_semaphore'].infer())
        semaphore_name = "threading.BoundedSemaphore"
        self.assertEqual(bounded_semaphore.qname(), semaphore_name)

        pool = next(module['pool'].infer())
        pool_name = "multiprocessing.pool.Pool"
        self.assertEqual(pool.qname(), pool_name)

        for attr in ('list', 'dict'):
            obj = next(module[attr].infer())
            self.assertEqual(obj.qname(),
                             "{}.{}".format(bases.BUILTINS, attr))

        array = next(module['array'].infer())
        self.assertEqual(array.qname(), "array.array")

        manager = next(module['manager'].infer())
        # Verify that we have these attributes
        self.assertTrue(manager.getattr('start'))
        self.assertTrue(manager.getattr('shutdown'))


class ThreadingBrainTest(unittest.TestCase):
    def test_lock(self):
        self._test_lock_object('Lock')

    def test_rlock(self):
        self._test_lock_object('RLock')

    def test_semaphore(self):
        self._test_lock_object('Semaphore')

    def test_boundedsemaphore(self):
        self._test_lock_object('BoundedSemaphore')

    def _test_lock_object(self, object_name):
        lock_instance = builder.extract_node("""
        import threading
        threading.{}()
        """.format(object_name))
        inferred = next(lock_instance.infer())
        self.assert_is_valid_lock(inferred)

    def assert_is_valid_lock(self, inferred):
        self.assertIsInstance(inferred, astroid.Instance)
        self.assertEqual(inferred.root().name, 'threading')
        for method in {'acquire', 'release', '__enter__', '__exit__'}:
            self.assertIsInstance(next(inferred.igetattr(method)), astroid.BoundMethod)


@unittest.skipUnless(HAS_ENUM,
                     'The enum module was only added in Python 3.4. Support for '
                     'older Python versions may be available through the enum34 '
                     'compatibility module.')
class EnumBrainTest(unittest.TestCase):

    def test_simple_enum(self):
        module = builder.parse("""
        import enum

        class MyEnum(enum.Enum):
            one = "one"
            two = "two"

            def mymethod(self, x):
                return 5

        """)

        enumeration = next(module['MyEnum'].infer())
        one = enumeration['one']
        self.assertEqual(one.pytype(), '.MyEnum.one')

        property_type = '{}.property'.format(bases.BUILTINS)
        for propname in ('name', 'value'):
            prop = next(iter(one.getattr(propname)))
            self.assertIn(property_type, prop.decoratornames())

        meth = one.getattr('mymethod')[0]
        self.assertIsInstance(meth, astroid.FunctionDef)

    def test_looks_like_enum_false_positive(self):
        # Test that a class named Enumeration is not considered a builtin enum.
        module = builder.parse('''
        class Enumeration(object):
            def __init__(self, name, enum_list):
                pass
            test = 42
        ''')
        enumeration = module['Enumeration']
        test = next(enumeration.igetattr('test'))
        self.assertEqual(test.value, 42)

    def test_enum_multiple_base_classes(self):
        module = builder.parse("""
        import enum

        class Mixin:
            pass

        class MyEnum(Mixin, enum.Enum):
            one = 1
        """)
        enumeration = next(module['MyEnum'].infer())
        one = enumeration['one']

        clazz = one.getattr('__class__')[0]
        self.assertTrue(clazz.is_subtype_of('.Mixin'),
                        'Enum instance should share base classes with generating class')

    def test_int_enum(self):
        module = builder.parse("""
        import enum

        class MyEnum(enum.IntEnum):
            one = 1
        """)

        enumeration = next(module['MyEnum'].infer())
        one = enumeration['one']

        clazz = one.getattr('__class__')[0]
        int_type = '{}.{}'.format(bases.BUILTINS, 'int')
        self.assertTrue(clazz.is_subtype_of(int_type),
                        'IntEnum based enums should be a subtype of int')

    def test_enum_func_form_is_class_not_instance(self):
        cls, instance = builder.extract_node('''
        from enum import Enum
        f = Enum('Audience', ['a', 'b', 'c'])
        f #@
        f(1) #@
        ''')
        inferred_cls = next(cls.infer())
        self.assertIsInstance(inferred_cls, bases.Instance)
        inferred_instance = next(instance.infer())
        self.assertIsInstance(inferred_instance, bases.Instance)
        self.assertIsInstance(next(inferred_instance.igetattr('name')), nodes.Const)
        self.assertIsInstance(next(inferred_instance.igetattr('value')), nodes.Const)

    def test_enum_func_form_iterable(self):
        instance = builder.extract_node('''
        from enum import Enum
        Animal = Enum('Animal', 'ant bee cat dog')
        Animal
        ''')
        inferred = next(instance.infer())
        self.assertIsInstance(inferred, astroid.Instance)
        self.assertTrue(inferred.getattr('__iter__'))

    def test_enum_func_form_subscriptable(self):
        instance, name = builder.extract_node('''
        from enum import Enum
        Animal = Enum('Animal', 'ant bee cat dog')
        Animal['ant'] #@
        Animal['ant'].name #@
        ''')
        instance = next(instance.infer())
        self.assertIsInstance(instance, astroid.Instance)

        inferred = next(name.infer())
        self.assertIsInstance(inferred, astroid.Const)

    def test_enum_func_form_has_dunder_members(self):
        instance = builder.extract_node('''
        from enum import Enum
        Animal = Enum('Animal', 'ant bee cat dog')
        for i in Animal.__members__:
            i #@
        ''')
        instance = next(instance.infer())
        self.assertIsInstance(instance, astroid.Const)
        self.assertIsInstance(instance.value, str)


@unittest.skipUnless(HAS_DATEUTIL, "This test requires the dateutil library.")
class DateutilBrainTest(unittest.TestCase):
    def test_parser(self):
        module = builder.parse("""
        from dateutil.parser import parse
        d = parse('2000-01-01')
        """)
        d_type = next(module['d'].infer())
        self.assertEqual(d_type.qname(), "datetime.datetime")


@unittest.skipUnless(HAS_PYTEST, "This test requires the pytest library.")
class PytestBrainTest(unittest.TestCase):

    def test_pytest(self):
        ast_node = builder.extract_node('''
        import pytest
        pytest #@
        ''')
        module = next(ast_node.infer())
        attrs = ['deprecated_call', 'warns', 'exit', 'fail', 'skip',
                 'importorskip', 'xfail', 'mark', 'raises', 'freeze_includes',
                 'set_trace', 'fixture', 'yield_fixture']
        if pytest.__version__.split('.')[0] == '3':
            attrs += ['approx', 'register_assert_rewrite']

        for attr in attrs:
            self.assertIn(attr, module)


def streams_are_fine():
    """Check if streams are being overwritten,
    for example, by pytest

    stream inference will not work if they are overwritten

    PY3 only
    """
    import io
    for stream in (sys.stdout, sys.stderr, sys.stdin):
        if not isinstance(stream, io.IOBase):
            return False
    return True


class IOBrainTest(unittest.TestCase):
    @unittest.skipUnless(
        streams_are_fine(),
        "Needs Python 3 io model / doesn't work with plain pytest."
        "use pytest -s for this test to work")
    def test_sys_streams(self):
        for name in {'stdout', 'stderr', 'stdin'}:
            node = astroid.extract_node('''
            import sys
            sys.{}
            '''.format(name))
            inferred = next(node.infer())
            buffer_attr = next(inferred.igetattr('buffer'))
            self.assertIsInstance(buffer_attr, astroid.Instance)
            self.assertEqual(buffer_attr.name, 'BufferedWriter')
            raw = next(buffer_attr.igetattr('raw'))
            self.assertIsInstance(raw, astroid.Instance)
            self.assertEqual(raw.name, 'FileIO')


@test_utils.require_version('3.6')
class TypingBrain(unittest.TestCase):

    def test_namedtuple_base(self):
        klass = builder.extract_node("""
        from typing import NamedTuple

        class X(NamedTuple("X", [("a", int), ("b", str), ("c", bytes)])):
           pass
        """)
        self.assertEqual(
            [anc.name for anc in klass.ancestors()],
            ['X', 'tuple', 'object'])
        for anc in klass.ancestors():
            self.assertFalse(anc.parent is None)

    def test_namedtuple_can_correcty_access_methods(self):
        klass, called = builder.extract_node("""
        from typing import NamedTuple

        class X(NamedTuple): #@
            a: int
            b: int
            def as_string(self):
                return '%s' % self.a
            def as_integer(self):
                return 2 + 3
        X().as_integer() #@
        """)
        self.assertEqual(len(klass.getattr('as_string')), 1)
        inferred = next(called.infer())
        self.assertIsInstance(inferred, astroid.Const)
        self.assertEqual(inferred.value, 5)

    def test_namedtuple_inference(self):
        klass = builder.extract_node("""
        from typing import NamedTuple

        class X(NamedTuple("X", [("a", int), ("b", str), ("c", bytes)])):
           pass
        """)
        base = next(base for base in klass.ancestors()
                    if base.name == 'X')
        self.assertSetEqual({"a", "b", "c"}, set(base.instance_attrs))

    def test_namedtuple_inference_nonliteral(self):
        # Note: NamedTuples in mypy only work with literals.
        klass = builder.extract_node("""
        from typing import NamedTuple

        name = "X"
        fields = [("a", int), ("b", str), ("c", bytes)]
        NamedTuple(name, fields)
        """)
        inferred = next(klass.infer())
        self.assertIsInstance(inferred, astroid.Instance)
        self.assertEqual(inferred.qname(), "typing.NamedTuple")

    def test_namedtuple_instance_attrs(self):
        result = builder.extract_node('''
        from typing import NamedTuple
        NamedTuple("A", [("a", int), ("b", str), ("c", bytes)])(1, 2, 3) #@
        ''')
        inferred = next(result.infer())
        for name, attr in inferred.instance_attrs.items():
            self.assertEqual(attr[0].attrname, name)

    def test_namedtuple_simple(self):
        result = builder.extract_node('''
        from typing import NamedTuple
        NamedTuple("A", [("a", int), ("b", str), ("c", bytes)])
        ''')
        inferred = next(result.infer())
        self.assertIsInstance(inferred, nodes.ClassDef)
        self.assertSetEqual({"a", "b", "c"}, set(inferred.instance_attrs))

    def test_namedtuple_few_args(self):
        result = builder.extract_node('''
        from typing import NamedTuple
        NamedTuple("A")
        ''')
        inferred = next(result.infer())
        self.assertIsInstance(inferred, astroid.Instance)
        self.assertEqual(inferred.qname(), "typing.NamedTuple")

    def test_namedtuple_few_fields(self):
        result = builder.extract_node('''
        from typing import NamedTuple
        NamedTuple("A", [("a",), ("b", str), ("c", bytes)])
        ''')
        inferred = next(result.infer())
        self.assertIsInstance(inferred, astroid.Instance)
        self.assertEqual(inferred.qname(), "typing.NamedTuple")

    def test_namedtuple_class_form(self):
        result = builder.extract_node('''
        from typing import NamedTuple

        class Example(NamedTuple):
            mything: int

        Example(mything=1)
        ''')
        inferred = next(result.infer())
        self.assertIsInstance(inferred, astroid.Instance)

    def test_typing_types(self):
        ast_nodes = builder.extract_node("""
        from typing import TypeVar, Iterable, Tuple, NewType, Dict, Union
        TypeVar('MyTypeVar', int, float, complex) #@
        Iterable[Tuple[MyTypeVar, MyTypeVar]] #@
        TypeVar('AnyStr', str, bytes) #@
        NewType('UserId', str) #@
        Dict[str, str] #@
        Union[int, str] #@
        """)
        for node in ast_nodes:
            inferred = next(node.infer())
            self.assertIsInstance(inferred, nodes.ClassDef, node.as_string())


class ReBrainTest(unittest.TestCase):
    def test_regex_flags(self):
        import re
        names = [name for name in dir(re) if name.isupper()]
        re_ast = MANAGER.ast_from_module_name('re')
        for name in names:
            self.assertIn(name, re_ast)
            self.assertEqual(next(re_ast[name].infer()).value, getattr(re, name))


@test_utils.require_version('3.6')
class BrainFStrings(unittest.TestCase):

    def test_no_crash_on_const_reconstruction(self):
        node = builder.extract_node('''
        max_width = 10

        test1 = f'{" ":{max_width+4}}'
        print(f'"{test1}"')

        test2 = f'[{"7":>{max_width}}:0]'
        test2
        ''')
        inferred = next(node.infer())
        self.assertIs(inferred, util.Uninferable)


@test_utils.require_version('3.6')
class BrainNamedtupleAnnAssignTest(unittest.TestCase):

    def test_no_crash_on_ann_assign_in_namedtuple(self):
        node = builder.extract_node('''
        from enum import Enum
        from typing import Optional

        class A(Enum):
            B: str = 'B'
        ''')
        inferred = next(node.infer())
        self.assertIsInstance(inferred, nodes.ClassDef)


class BrainUUIDTest(unittest.TestCase):

    def test_uuid_has_int_member(self):
        node = builder.extract_node('''
        import uuid
        u = uuid.UUID('{12345678-1234-5678-1234-567812345678}')
        u.int
        ''')
        inferred = next(node.infer())
        self.assertIsInstance(inferred, nodes.Const)


@unittest.skipUnless(HAS_ATTR, "These tests require the attr library")
class AttrsTest(unittest.TestCase):
    def test_attr_transform(self):
        module = astroid.parse("""
        import attr

        @attr.s
        class Foo:

            d = attr.ib(attr.Factory(dict))

        f = Foo()
        f.d['answer'] = 42

        @attr.s(slots=True)
        class Bar:
            d = attr.ib(attr.Factory(dict))

        g = Bar()
        g.d['answer'] = 42
        """)

        for name in ('f', 'g'):
            should_be_unknown = next(module.getattr(name)[0].infer()).getattr('d')[0]
            self.assertIsInstance(should_be_unknown, astroid.Unknown)

    def test_special_attributes(self):
        """Make sure special attrs attributes exist"""

        code = """
        import attr

        @attr.s
        class Foo:
            pass
        Foo()
        """
        foo_inst = next(astroid.extract_node(code).infer())
        [attr_node] = foo_inst.getattr("__attrs_attrs__")
        # Prevents https://github.com/PyCQA/pylint/issues/1884
        assert isinstance(attr_node, nodes.Unknown)

    def test_dont_consider_assignments_but_without_attrs(self):
        code = '''
        import attr

        class Cls: pass
        @attr.s
        class Foo:
            temp = Cls()
            temp.prop = 5
            bar_thing = attr.ib(default=temp)
        Foo()
        '''
        next(astroid.extract_node(code).infer())


class RandomSampleTest(unittest.TestCase):

    def test_inferred_successfully(self):
        node = astroid.extract_node('''
        import random
        random.sample([1, 2], 2) #@
        ''')
        inferred = next(node.infer())
        self.assertIsInstance(inferred, astroid.List)
        elems = sorted(elem.value for elem in inferred.elts)
        self.assertEqual(elems, [1, 2])


class SubprocessTest(unittest.TestCase):
    """Test subprocess brain"""
    # TODO Add more tests so that we can some day
    # Remove this brain when all the tests work without the brain
    @unittest.skipIf(sys.version_info < (3, 3),
                     reason="Python 2.7 subprocess doesnt have args")
    def test_subprocess_args(self):
        """Make sure the args attribute exists for Popen

        Test for https://github.com/PyCQA/pylint/issues/1860"""
        name = astroid.extract_node("""
        import subprocess
        p = subprocess.Popen(['ls'])
        p #@
        """)
        [inst] = name.inferred()
        self.assertIsInstance(next(inst.igetattr("args")), nodes.List)


class TestIsinstanceInference:
    """Test isinstance builtin inference"""

    def test_type_type(self):
        assert _get_result("isinstance(type, type)") == "True"

    def test_object_type(self):
        assert _get_result("isinstance(object, type)") == "True"

    def test_type_object(self):
        assert _get_result("isinstance(type, object)") == "True"

    def test_isinstance_int_true(self):
        """Make sure isinstance can check builtin int types"""
        assert _get_result("isinstance(1, int)") == "True"

    def test_isinstance_int_false(self):
        assert _get_result("isinstance('a', int)") == "False"

    def test_isinstance_object_true(self):
        assert _get_result("""
        class Bar(object):
            pass
        isinstance(Bar(), object)
        """) == "True"

    def test_isinstance_object_true3(self):
        assert _get_result("""
        class Bar(object):
            pass
        isinstance(Bar(), Bar)
        """) == "True"

    def test_isinstance_class_false(self):
        assert _get_result("""
        class Foo(object):
            pass
        class Bar(object):
            pass
        isinstance(Bar(), Foo)
        """) == "False"

    def test_isinstance_type_false(self):
        assert _get_result("""
        class Bar(object):
            pass
        isinstance(Bar(), type)
        """) == "False"

    def test_isinstance_str_true(self):
        """Make sure isinstance can check bultin str types"""
        assert _get_result("isinstance('a', str)") == "True"

    def test_isinstance_str_false(self):
        assert _get_result("isinstance(1, str)") == "False"

    def test_isinstance_tuple_argument(self):
        """obj just has to be an instance of ANY class/type on the right"""
        assert _get_result("isinstance(1, (str, int))") == "True"

    def test_isinstance_type_false2(self):
        assert _get_result("""
        isinstance(1, type)
        """) == "False"

    def test_isinstance_object_true2(self):
        assert _get_result("""
        class Bar(type):
            pass
        mainbar = Bar("Bar", tuple(), {})
        isinstance(mainbar, object)
        """) == "True"

    def test_isinstance_type_true(self):
        assert _get_result("""
        class Bar(type):
            pass
        mainbar = Bar("Bar", tuple(), {})
        isinstance(mainbar, type)
        """) == "True"

    def test_isinstance_edge_case(self):
        """isinstance allows bad type short-circuting"""
        assert _get_result("isinstance(1, (int, 1))") == "True"

    def test_uninferable_bad_type(self):
        """The second argument must be a class or a tuple of classes"""
        with pytest.raises(astroid.InferenceError):
            _get_result_node("isinstance(int, 1)")

    def test_uninferable_keywords(self):
        """isinstance does not allow keywords"""
        with pytest.raises(astroid.InferenceError):
            _get_result_node("isinstance(1, class_or_tuple=int)")

    def test_too_many_args(self):
        """isinstance must have two arguments"""
        with pytest.raises(astroid.InferenceError):
            _get_result_node("isinstance(1, int, str)")

    def test_first_param_is_uninferable(self):
        with pytest.raises(astroid.InferenceError):
            _get_result_node('isinstance(something, int)')


class TestIssubclassBrain:
    """Test issubclass() builtin inference"""

    def test_type_type(self):
        assert _get_result("issubclass(type, type)") == "True"

    def test_object_type(self):
        assert _get_result("issubclass(object, type)") == "False"

    def test_type_object(self):
        assert _get_result("issubclass(type, object)") == "True"

    def test_issubclass_same_class(self):
        assert _get_result("issubclass(int, int)") == "True"

    def test_issubclass_not_the_same_class(self):
        assert _get_result("issubclass(str, int)") == "False"

    def test_issubclass_object_true(self):
        assert _get_result("""
        class Bar(object):
            pass
        issubclass(Bar, object)
        """) == "True"

    def test_issubclass_same_user_defined_class(self):
        assert _get_result("""
        class Bar(object):
            pass
        issubclass(Bar, Bar)
        """) == "True"

    def test_issubclass_different_user_defined_classes(self):
        assert _get_result("""
        class Foo(object):
            pass
        class Bar(object):
            pass
        issubclass(Bar, Foo)
        """) == "False"

    def test_issubclass_type_false(self):
        assert _get_result("""
        class Bar(object):
            pass
        issubclass(Bar, type)
        """) == "False"

    def test_isinstance_tuple_argument(self):
        """obj just has to be a subclass of ANY class/type on the right"""
        assert _get_result("issubclass(int, (str, int))") == "True"

    def test_isinstance_object_true2(self):
        assert _get_result("""
        class Bar(type):
            pass
        issubclass(Bar, object)
        """) == "True"

    def test_issubclass_short_circuit(self):
        """issubclasss allows bad type short-circuting"""
        assert _get_result("issubclass(int, (int, 1))") == "True"

    def test_uninferable_bad_type(self):
        """The second argument must be a class or a tuple of classes"""
        # Should I subclass
        with pytest.raises(astroid.InferenceError):
            _get_result_node("issubclass(int, 1)")

    def test_uninferable_keywords(self):
        """issubclass does not allow keywords"""
        with pytest.raises(astroid.InferenceError):
            _get_result_node("issubclass(int, class_or_tuple=int)")

    def test_too_many_args(self):
        """issubclass must have two arguments"""
        with pytest.raises(astroid.InferenceError):
            _get_result_node("issubclass(int, int, str)")


def _get_result_node(code):
    node = next(astroid.extract_node(code).infer())
    return node


def _get_result(code):
    return _get_result_node(code).as_string()


class TestLenBuiltinInference:
    def test_len_list(self):
        # Uses .elts
        node = astroid.extract_node("""
        len(['a','b','c'])
        """)
        node = next(node.infer())
        assert node.as_string() == '3'
        assert isinstance(node, nodes.Const)

    def test_len_tuple(self):
        node = astroid.extract_node("""
        len(('a','b','c'))
        """)
        node = next(node.infer())
        assert node.as_string() == '3'

    def test_len_var(self):
        # Make sure argument is inferred
        node = astroid.extract_node("""
        a = [1,2,'a','b','c']
        len(a)
        """)
        node = next(node.infer())
        assert node.as_string() == '5'

    def test_len_dict(self):
        # Uses .items
        node = astroid.extract_node("""
        a = {'a': 1, 'b': 2}
        len(a)
        """)
        node = next(node.infer())
        assert node.as_string() == '2'

    def test_len_set(self):
        node = astroid.extract_node("""
        len({'a'})
        """)
        inferred_node = next(node.infer())
        assert inferred_node.as_string() == '1'

    def test_len_object(self):
        """Test len with objects that implement the len protocol"""
        node = astroid.extract_node("""
        class A:
            def __len__(self):
                return 57
        len(A())
        """)
        inferred_node = next(node.infer())
        assert inferred_node.as_string() == '57'

    def test_len_class_with_metaclass(self):
        """Make sure proper len method is located"""
        cls_node, inst_node = astroid.extract_node("""
        class F2(type):
            def __new__(cls, name, bases, attrs):
                return super().__new__(cls, name, bases, {})
            def __len__(self):
                return 57
        class F(metaclass=F2):
            def __len__(self):
                return 4
        len(F) #@
        len(F()) #@
        """)
        assert next(cls_node.infer()).as_string() == '57'
        assert next(inst_node.infer()).as_string() == '4'

    def test_len_object_failure(self):
        """If taking the length of a class, do not use an instance method"""
        node = astroid.extract_node("""
        class F:
            def __len__(self):
                return 57
        len(F)
        """)
        with pytest.raises(astroid.InferenceError):
            next(node.infer())

    def test_len_string(self):
        node = astroid.extract_node("""
        len("uwu")
        """)
        assert next(node.infer()).as_string() == "3"

    def test_len_generator_failure(self):
        node = astroid.extract_node("""
        def gen():
            yield 'a'
            yield 'b'
        len(gen())
        """)
        with pytest.raises(astroid.InferenceError):
            next(node.infer())

    def test_len_failure_missing_variable(self):
        node = astroid.extract_node("""
        len(a)
        """)
        with pytest.raises(astroid.InferenceError):
            next(node.infer())

    def test_len_bytes(self):
        node = astroid.extract_node("""
        len(b'uwu')
        """)
        assert next(node.infer()).as_string() == '3'


    @pytest.mark.xfail(reason="Can't retrieve subclassed type value ")
    def test_int_subclass_result(self):
        """I am unable to figure out the value of an
        object which subclasses int"""
        node = astroid.extract_node("""
        class IntSubclass(int):
            pass

        class F:
            def __len__(self):
                return IntSubclass(5)
        len(F())
        """)
        assert next(node.infer()).as_string() == '5'

    @pytest.mark.xfail(reason="Can't use list special astroid fields")
    def test_int_subclass_argument(self):
        """I am unable to access the length of a object which
        subclasses list"""
        node = astroid.extract_node("""
        class ListSubclass(list):
            pass
        len(ListSubclass([1,2,3,4,4]))
        """)
        assert next(node.infer()).as_string() == '5'

    def test_len_builtin_inference_attribute_error_str(self):
        """Make sure len builtin doesn't raise an AttributeError
        on instances of str or bytes

        See https://github.com/PyCQA/pylint/issues/1942
        """
        code = 'len(str("F"))'
        try:
            next(astroid.extract_node(code).infer())
        except astroid.InferenceError:
            pass


def test_infer_str():
    ast_nodes = astroid.extract_node('''
    str(s) #@
    str('a') #@
    str(some_object()) #@
    ''')
    for node in ast_nodes:
        inferred = next(node.infer())
        assert isinstance(inferred, astroid.Const)

    node = astroid.extract_node('''
    str(s='') #@
    ''')
    inferred = next(node.infer())
    assert isinstance(inferred, astroid.Instance)
    assert inferred.qname() == 'builtins.str'


def test_infer_int():
    ast_nodes = astroid.extract_node('''
    int(0) #@
    int('1') #@
    ''')
    for node in ast_nodes:
        inferred = next(node.infer())
        assert isinstance(inferred, astroid.Const)

    ast_nodes = astroid.extract_node('''
    int(s='') #@
    int('2.5') #@
    int('something else') #@
    int(unknown) #@
    int(b'a') #@
    ''')
    for node in ast_nodes:
        inferred = next(node.infer())
        assert isinstance(inferred, astroid.Instance)
        assert inferred.qname() == 'builtins.int'


def test_infer_dict_from_keys():
    bad_nodes = astroid.extract_node('''
    dict.fromkeys() #@
    dict.fromkeys(1, 2, 3) #@
    dict.fromkeys(a=1) #@
    ''')
    for node in bad_nodes:
        with pytest.raises(astroid.InferenceError):
            next(node.infer())

    # Test uninferable values
    good_nodes = astroid.extract_node('''
    from unknown import Unknown
    dict.fromkeys(some_value) #@
    dict.fromkeys(some_other_value) #@
    dict.fromkeys([Unknown(), Unknown()]) #@
    dict.fromkeys([Unknown(), Unknown()]) #@
    ''')
    for node in good_nodes:
        inferred = next(node.infer())
        assert isinstance(inferred, astroid.Dict)
        assert inferred.items == []

    # Test inferrable values

    # from a dictionary's keys
    from_dict = astroid.extract_node('''
    dict.fromkeys({'a':2, 'b': 3, 'c': 3}) #@
    ''')
    inferred = next(from_dict.infer())
    assert isinstance(inferred, astroid.Dict)
    itered = inferred.itered()
    assert all(isinstance(elem, astroid.Const) for elem in itered)
    actual_values = [elem.value for elem in itered]
    assert sorted(actual_values) == ['a', 'b', 'c']

    # from a string
    from_string = astroid.extract_node('''
    dict.fromkeys('abc')
    ''')
    inferred = next(from_string.infer())
    assert isinstance(inferred, astroid.Dict)
    itered = inferred.itered()
    assert all(isinstance(elem, astroid.Const) for elem in itered)
    actual_values = [elem.value for elem in itered]
    assert sorted(actual_values) == ['a', 'b', 'c']

    # from bytes
    from_bytes = astroid.extract_node('''
    dict.fromkeys(b'abc')
    ''')
    inferred = next(from_bytes.infer())
    assert isinstance(inferred, astroid.Dict)
    itered = inferred.itered()
    assert all(isinstance(elem, astroid.Const) for elem in itered)
    actual_values = [elem.value for elem in itered]
    assert sorted(actual_values) == [97, 98, 99]

    # From list/set/tuple
    from_others = astroid.extract_node('''
    dict.fromkeys(('a', 'b', 'c')) #@
    dict.fromkeys(['a', 'b', 'c']) #@
    dict.fromkeys({'a', 'b', 'c'}) #@
    ''')
    for node in from_others:
        inferred = next(node.infer())
        assert isinstance(inferred, astroid.Dict)
        itered = inferred.itered()
        assert all(isinstance(elem, astroid.Const) for elem in itered)
        actual_values = [elem.value for elem in itered]
        assert sorted(actual_values) == ['a', 'b', 'c']


if __name__ == '__main__':
    unittest.main()
