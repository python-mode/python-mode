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
import os
import platform
import sys
import unittest

import six

from astroid import exceptions
from astroid import manager
from astroid.tests import resources


BUILTINS = six.moves.builtins.__name__


def _get_file_from_object(obj):
    if platform.python_implementation() == 'Jython':
        return obj.__file__.split("$py.class")[0] + ".py"
    if sys.version_info > (3, 0):
        return obj.__file__
    if not obj.__file__.endswith(".py"):
        return obj.__file__[:-1]
    return obj.__file__


class AstroidManagerTest(resources.SysPathSetup,
                         resources.AstroidCacheSetupMixin,
                         unittest.TestCase):

    def setUp(self):
        super(AstroidManagerTest, self).setUp()
        self.manager = manager.AstroidManager()
        self.manager.clear_cache(self._builtins) # take care of borg

    def test_ast_from_file(self):
        filepath = unittest.__file__
        astroid = self.manager.ast_from_file(filepath)
        self.assertEqual(astroid.name, 'unittest')
        self.assertIn('unittest', self.manager.astroid_cache)

    def test_ast_from_file_cache(self):
        filepath = unittest.__file__
        self.manager.ast_from_file(filepath)
        astroid = self.manager.ast_from_file('unhandledName', 'unittest')
        self.assertEqual(astroid.name, 'unittest')
        self.assertIn('unittest', self.manager.astroid_cache)

    def test_ast_from_file_astro_builder(self):
        filepath = unittest.__file__
        astroid = self.manager.ast_from_file(filepath, None, True, True)
        self.assertEqual(astroid.name, 'unittest')
        self.assertIn('unittest', self.manager.astroid_cache)

    def test_ast_from_file_name_astro_builder_exception(self):
        self.assertRaises(exceptions.AstroidBuildingException,
                          self.manager.ast_from_file, 'unhandledName')

    def test_do_not_expose_main(self):
        obj = self.manager.ast_from_module_name('__main__')
        self.assertEqual(obj.name, '__main__')
        self.assertEqual(obj.items(), [])

    def test_ast_from_module_name(self):
        astroid = self.manager.ast_from_module_name('unittest')
        self.assertEqual(astroid.name, 'unittest')
        self.assertIn('unittest', self.manager.astroid_cache)

    def test_ast_from_module_name_not_python_source(self):
        astroid = self.manager.ast_from_module_name('time')
        self.assertEqual(astroid.name, 'time')
        self.assertIn('time', self.manager.astroid_cache)
        self.assertEqual(astroid.pure_python, False)

    def test_ast_from_module_name_astro_builder_exception(self):
        self.assertRaises(exceptions.AstroidBuildingException,
                          self.manager.ast_from_module_name,
                          'unhandledModule')

    def _test_ast_from_zip(self, archive):
        origpath = sys.path[:]
        sys.modules.pop('mypypa', None)
        archive_path = resources.find(archive)
        sys.path.insert(0, archive_path)
        try:
            module = self.manager.ast_from_module_name('mypypa')
            self.assertEqual(module.name, 'mypypa')
            end = os.path.join(archive, 'mypypa')
            self.assertTrue(module.source_file.endswith(end),
                            "%s doesn't endswith %s" % (module.source_file, end))
        finally:
            # remove the module, else after importing egg, we don't get the zip
            if 'mypypa' in self.manager.astroid_cache:
                del self.manager.astroid_cache['mypypa']
                del self.manager._mod_file_cache[('mypypa', None)]
            if archive_path in sys.path_importer_cache:
                del sys.path_importer_cache[archive_path]
            sys.path = origpath

    def test_ast_from_module_name_egg(self):
        self._test_ast_from_zip(
            os.path.sep.join(['data', os.path.normcase('MyPyPa-0.1.0-py2.5.egg')])
        )

    def test_ast_from_module_name_zip(self):
        self._test_ast_from_zip(
            os.path.sep.join(['data', os.path.normcase('MyPyPa-0.1.0-py2.5.zip')])
        )

    def test_zip_import_data(self):
        """check if zip_import_data works"""
        filepath = resources.find('data/MyPyPa-0.1.0-py2.5.zip/mypypa')
        astroid = self.manager.zip_import_data(filepath)
        self.assertEqual(astroid.name, 'mypypa')

    def test_zip_import_data_without_zipimport(self):
        """check if zip_import_data return None without zipimport"""
        self.assertEqual(self.manager.zip_import_data('path'), None)

    def test_file_from_module(self):
        """check if the unittest filepath is equals to the result of the method"""
        self.assertEqual(
            _get_file_from_object(unittest),
            self.manager.file_from_module_name('unittest', None)[0])

    def test_file_from_module_name_astro_building_exception(self):
        """check if the method launch a exception with a wrong module name"""
        self.assertRaises(exceptions.AstroidBuildingException,
                          self.manager.file_from_module_name, 'unhandledModule', None)

    def test_ast_from_module(self):
        astroid = self.manager.ast_from_module(unittest)
        self.assertEqual(astroid.pure_python, True)
        import time
        astroid = self.manager.ast_from_module(time)
        self.assertEqual(astroid.pure_python, False)

    def test_ast_from_module_cache(self):
        """check if the module is in the cache manager"""
        astroid = self.manager.ast_from_module(unittest)
        self.assertEqual(astroid.name, 'unittest')
        self.assertIn('unittest', self.manager.astroid_cache)

    def test_ast_from_class(self):
        astroid = self.manager.ast_from_class(int)
        self.assertEqual(astroid.name, 'int')
        self.assertEqual(astroid.parent.frame().name, BUILTINS)

        astroid = self.manager.ast_from_class(object)
        self.assertEqual(astroid.name, 'object')
        self.assertEqual(astroid.parent.frame().name, BUILTINS)
        self.assertIn('__setattr__', astroid)

    def test_ast_from_class_with_module(self):
        """check if the method works with the module name"""
        astroid = self.manager.ast_from_class(int, int.__module__)
        self.assertEqual(astroid.name, 'int')
        self.assertEqual(astroid.parent.frame().name, BUILTINS)

        astroid = self.manager.ast_from_class(object, object.__module__)
        self.assertEqual(astroid.name, 'object')
        self.assertEqual(astroid.parent.frame().name, BUILTINS)
        self.assertIn('__setattr__', astroid)

    def test_ast_from_class_attr_error(self):
        """give a wrong class at the ast_from_class method"""
        self.assertRaises(exceptions.AstroidBuildingException,
                          self.manager.ast_from_class, None)

    def testFailedImportHooks(self):
        def hook(modname):
            if modname == 'foo.bar':
                return unittest
            else:
                raise exceptions.AstroidBuildingException()

        with self.assertRaises(exceptions.AstroidBuildingException):
            self.manager.ast_from_module_name('foo.bar')
        self.manager.register_failed_import_hook(hook)
        self.assertEqual(unittest, self.manager.ast_from_module_name('foo.bar'))
        with self.assertRaises(exceptions.AstroidBuildingException):
            self.manager.ast_from_module_name('foo.bar.baz')
        del self.manager._failed_import_hooks[0]


class BorgAstroidManagerTC(unittest.TestCase):

    def test_borg(self):
        """test that the AstroidManager is really a borg, i.e. that two different
        instances has same cache"""
        first_manager = manager.AstroidManager()
        built = first_manager.ast_from_module_name(BUILTINS)

        second_manager = manager.AstroidManager()
        second_built = second_manager.ast_from_module_name(BUILTINS)
        self.assertIs(built, second_built)


if __name__ == '__main__':
    unittest.main()
