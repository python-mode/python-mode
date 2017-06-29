# copyright 2003-2014 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
# contact http://www.logilab.fr/ -- mailto:contact@logilab.fr
#
# This file is part of astroid.
#
# astroid is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 2.1 of the License, or (at your option) any
# later version.
#
# astroid is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with astroid.  If not, see <http://www.gnu.org/licenses/>.
"""
unit tests for module modutils (module manipulation utilities)
"""
import os
import sys
import unittest

from astroid import modutils
from astroid.tests import resources


def _get_file_from_object(obj):
    return modutils._path_from_filename(obj.__file__)


class ModuleFileTest(unittest.TestCase):
    package = "mypypa"

    def tearDown(self):
        for k in list(sys.path_importer_cache.keys()):
            if 'MyPyPa' in k:
                del sys.path_importer_cache[k]

    def test_find_zipped_module(self):
        mtype, mfile = modutils._module_file(
            [self.package], [resources.find('data/MyPyPa-0.1.0-py2.5.zip')])
        self.assertEqual(mtype, modutils.PY_ZIPMODULE)
        self.assertEqual(mfile.split(os.sep)[-3:], ["data", "MyPyPa-0.1.0-py2.5.zip", self.package])

    def test_find_egg_module(self):
        mtype, mfile = modutils._module_file(
            [self.package], [resources.find('data/MyPyPa-0.1.0-py2.5.egg')])
        self.assertEqual(mtype, modutils.PY_ZIPMODULE)
        self.assertEqual(mfile.split(os.sep)[-3:], ["data", "MyPyPa-0.1.0-py2.5.egg", self.package])


class LoadModuleFromNameTest(unittest.TestCase):
    """ load a python module from it's name """

    def test_knownValues_load_module_from_name_1(self):
        self.assertEqual(modutils.load_module_from_name('sys'), sys)

    def test_knownValues_load_module_from_name_2(self):
        self.assertEqual(modutils.load_module_from_name('os.path'), os.path)

    def test_raise_load_module_from_name_1(self):
        self.assertRaises(ImportError,
                          modutils.load_module_from_name, 'os.path', use_sys=0)


class GetModulePartTest(unittest.TestCase):
    """given a dotted name return the module part of the name"""

    def test_knownValues_get_module_part_1(self):
        self.assertEqual(modutils.get_module_part('astroid.modutils'),
                         'astroid.modutils')

    def test_knownValues_get_module_part_2(self):
        self.assertEqual(modutils.get_module_part('astroid.modutils.get_module_part'),
                         'astroid.modutils')

    def test_knownValues_get_module_part_3(self):
        """relative import from given file"""
        self.assertEqual(modutils.get_module_part('node_classes.AssName',
                                                  modutils.__file__), 'node_classes')

    def test_knownValues_get_compiled_module_part(self):
        self.assertEqual(modutils.get_module_part('math.log10'), 'math')
        self.assertEqual(modutils.get_module_part('math.log10', __file__), 'math')

    def test_knownValues_get_builtin_module_part(self):
        self.assertEqual(modutils.get_module_part('sys.path'), 'sys')
        self.assertEqual(modutils.get_module_part('sys.path', '__file__'), 'sys')

    def test_get_module_part_exception(self):
        self.assertRaises(ImportError, modutils.get_module_part, 'unknown.module',
                          modutils.__file__)


class ModPathFromFileTest(unittest.TestCase):
    """ given an absolute file path return the python module's path as a list """

    def test_knownValues_modpath_from_file_1(self):
        from xml.etree import ElementTree
        self.assertEqual(modutils.modpath_from_file(ElementTree.__file__),
                         ['xml', 'etree', 'ElementTree'])

    def test_knownValues_modpath_from_file_2(self):
        self.assertEqual(modutils.modpath_from_file('unittest_modutils.py',
                                                    {os.getcwd(): 'arbitrary.pkg'}),
                         ['arbitrary', 'pkg', 'unittest_modutils'])

    def test_raise_modpath_from_file_Exception(self):
        self.assertRaises(Exception, modutils.modpath_from_file, '/turlututu')


class LoadModuleFromPathTest(resources.SysPathSetup, unittest.TestCase):

    def test_do_not_load_twice(self):
        modutils.load_module_from_modpath(['data', 'lmfp', 'foo'])
        modutils.load_module_from_modpath(['data', 'lmfp'])
        self.assertEqual(len(sys.just_once), 1)
        del sys.just_once


class FileFromModPathTest(resources.SysPathSetup, unittest.TestCase):
    """given a mod path (i.e. splited module / package name), return the
    corresponding file, giving priority to source file over precompiled file
    if it exists"""

    def test_site_packages(self):
        filename = _get_file_from_object(modutils)
        result = modutils.file_from_modpath(['astroid', 'modutils'])
        self.assertEqual(os.path.realpath(result), os.path.realpath(filename))

    def test_std_lib(self):
        from os import path
        self.assertEqual(os.path.realpath(modutils.file_from_modpath(['os', 'path']).replace('.pyc', '.py')),
                         os.path.realpath(path.__file__.replace('.pyc', '.py')))

    def test_xmlplus(self):
        try:
            # don't fail if pyxml isn't installed
            from xml.dom import ext
        except ImportError:
            pass
        else:
            self.assertEqual(os.path.realpath(modutils.file_from_modpath(['xml', 'dom', 'ext']).replace('.pyc', '.py')),
                             os.path.realpath(ext.__file__.replace('.pyc', '.py')))

    def test_builtin(self):
        self.assertEqual(modutils.file_from_modpath(['sys']),
                         None)


    def test_unexisting(self):
        self.assertRaises(ImportError, modutils.file_from_modpath, ['turlututu'])

    def test_unicode_in_package_init(self):
        # file_from_modpath should not crash when reading an __init__
        # file with unicode characters.
        modutils.file_from_modpath(["data", "unicode_package", "core"])


class GetSourceFileTest(unittest.TestCase):

    def test(self):
        filename = _get_file_from_object(os.path)
        self.assertEqual(modutils.get_source_file(os.path.__file__),
                         os.path.normpath(filename))

    def test_raise(self):
        self.assertRaises(modutils.NoSourceFile, modutils.get_source_file, 'whatever')


class StandardLibModuleTest(resources.SysPathSetup, unittest.TestCase):
    """
    return true if the module may be considered as a module from the standard
    library
    """

    def test_datetime(self):
        # This is an interesting example, since datetime, on pypy,
        # is under lib_pypy, rather than the usual Lib directory.
        self.assertTrue(modutils.is_standard_module('datetime'))

    def test_builtins(self):
        if sys.version_info < (3, 0):
            self.assertEqual(modutils.is_standard_module('__builtin__'), True)
            self.assertEqual(modutils.is_standard_module('builtins'), False)
        else:
            self.assertEqual(modutils.is_standard_module('__builtin__'), False)
            self.assertEqual(modutils.is_standard_module('builtins'), True)

    def test_builtin(self):
        self.assertEqual(modutils.is_standard_module('sys'), True)
        self.assertEqual(modutils.is_standard_module('marshal'), True)

    def test_nonstandard(self):
        self.assertEqual(modutils.is_standard_module('astroid'), False)

    def test_unknown(self):
        self.assertEqual(modutils.is_standard_module('unknown'), False)

    def test_4(self):
        self.assertEqual(modutils.is_standard_module('hashlib'), True)
        self.assertEqual(modutils.is_standard_module('pickle'), True)
        self.assertEqual(modutils.is_standard_module('email'), True)
        self.assertEqual(modutils.is_standard_module('io'), sys.version_info >= (2, 6))
        self.assertEqual(modutils.is_standard_module('StringIO'), sys.version_info < (3, 0))
        self.assertEqual(modutils.is_standard_module('unicodedata'), True)

    def test_custom_path(self):
        datadir = resources.find('')
        if datadir.startswith(modutils.EXT_LIB_DIR):
            self.skipTest('known breakage of is_standard_module on installed package')
        self.assertEqual(modutils.is_standard_module('data.module', (datadir,)), True)
        self.assertEqual(modutils.is_standard_module('data.module', (os.path.abspath(datadir),)), True)

    def test_failing_edge_cases(self):
        from xml import etree
        # using a subpackage/submodule path as std_path argument
        self.assertEqual(modutils.is_standard_module('xml.etree', etree.__path__), False)
        # using a module + object name as modname argument
        self.assertEqual(modutils.is_standard_module('sys.path'), True)
        # this is because only the first package/module is considered
        self.assertEqual(modutils.is_standard_module('sys.whatever'), True)
        self.assertEqual(modutils.is_standard_module('xml.whatever', etree.__path__), False)


class IsRelativeTest(unittest.TestCase):


    def test_knownValues_is_relative_1(self):
        import email
        self.assertEqual(modutils.is_relative('utils', email.__path__[0]),
                         True)

    def test_knownValues_is_relative_2(self):
        from xml.etree import ElementTree
        self.assertEqual(modutils.is_relative('ElementPath', ElementTree.__file__),
                         True)

    def test_knownValues_is_relative_3(self):
        import astroid
        self.assertEqual(modutils.is_relative('astroid', astroid.__path__[0]),
                         False)


class GetModuleFilesTest(unittest.TestCase):

    def test_get_module_files_1(self):
        package = resources.find('data/find_test')
        modules = set(modutils.get_module_files(package, []))
        expected = ['__init__.py', 'module.py', 'module2.py',
                    'noendingnewline.py', 'nonregr.py']
        self.assertEqual(modules,
                         {os.path.join(package, x) for x in expected})

    def test_load_module_set_attribute(self):
        import xml.etree.ElementTree
        import xml
        del xml.etree.ElementTree
        del sys.modules['xml.etree.ElementTree']
        m = modutils.load_module_from_modpath(['xml', 'etree', 'ElementTree'])
        self.assertTrue(hasattr(xml, 'etree'))
        self.assertTrue(hasattr(xml.etree, 'ElementTree'))
        self.assertTrue(m is xml.etree.ElementTree)


if __name__ == '__main__':
    unittest.main()
