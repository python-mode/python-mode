# copyright 2003-2013 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
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
"""astroid manager: avoid multiple astroid build of a same module when
possible by providing a class responsible to get astroid representation
from various source and using a cache of built modules)
"""
from __future__ import print_function

import imp
import os
import zipimport

from astroid import exceptions
from astroid import modutils
from astroid import transforms


def safe_repr(obj):
    try:
        return repr(obj)
    except Exception: # pylint: disable=broad-except
        return '???'


class AstroidManager(object):
    """the astroid manager, responsible to build astroid from files
     or modules.

    Use the Borg pattern.
    """

    name = 'astroid loader'
    brain = {}

    def __init__(self):
        self.__dict__ = AstroidManager.brain
        if not self.__dict__:
            # NOTE: cache entries are added by the [re]builder
            self.astroid_cache = {}
            self._mod_file_cache = {}
            self._failed_import_hooks = []
            self.always_load_extensions = False
            self.optimize_ast = False
            self.extension_package_whitelist = set()
            self._transform = transforms.TransformVisitor()

            # Export these APIs for convenience
            self.register_transform = self._transform.register_transform
            self.unregister_transform = self._transform.unregister_transform

    def visit_transforms(self, node):
        """Visit the transforms and apply them to the given *node*."""
        return self._transform.visit(node)

    def ast_from_file(self, filepath, modname=None, fallback=True, source=False):
        """given a module name, return the astroid object"""
        try:
            filepath = modutils.get_source_file(filepath, include_no_ext=True)
            source = True
        except modutils.NoSourceFile:
            pass
        if modname is None:
            try:
                modname = '.'.join(modutils.modpath_from_file(filepath))
            except ImportError:
                modname = filepath
        if modname in self.astroid_cache and self.astroid_cache[modname].source_file == filepath:
            return self.astroid_cache[modname]
        if source:
            from astroid.builder import AstroidBuilder
            return AstroidBuilder(self).file_build(filepath, modname)
        elif fallback and modname:
            return self.ast_from_module_name(modname)
        raise exceptions.AstroidBuildingException(
            'unable to get astroid for file %s' % filepath)

    def _build_stub_module(self, modname):
        from astroid.builder import AstroidBuilder
        return AstroidBuilder(self).string_build('', modname)

    def _can_load_extension(self, modname):
        if self.always_load_extensions:
            return True
        if modutils.is_standard_module(modname):
            return True
        parts = modname.split('.')
        return any(
            '.'.join(parts[:x]) in self.extension_package_whitelist
            for x in range(1, len(parts) + 1))

    def ast_from_module_name(self, modname, context_file=None):
        """given a module name, return the astroid object"""
        if modname in self.astroid_cache:
            return self.astroid_cache[modname]
        if modname == '__main__':
            return self._build_stub_module(modname)
        old_cwd = os.getcwd()
        if context_file:
            os.chdir(os.path.dirname(context_file))
        try:
            filepath, mp_type = self.file_from_module_name(modname, context_file)
            if mp_type == modutils.PY_ZIPMODULE:
                module = self.zip_import_data(filepath)
                if module is not None:
                    return module
            elif mp_type in (imp.C_BUILTIN, imp.C_EXTENSION):
                if mp_type == imp.C_EXTENSION and not self._can_load_extension(modname):
                    return self._build_stub_module(modname)
                try:
                    module = modutils.load_module_from_name(modname)
                except Exception as ex:
                    msg = 'Unable to load module %s (%s)' % (modname, ex)
                    raise exceptions.AstroidBuildingException(msg)
                return self.ast_from_module(module, modname)
            elif mp_type == imp.PY_COMPILED:
                msg = "Unable to load compiled module %s" % (modname,)
                raise exceptions.AstroidBuildingException(msg)
            if filepath is None:
                msg = "Unable to load module %s" % (modname,)
                raise exceptions.AstroidBuildingException(msg)
            return self.ast_from_file(filepath, modname, fallback=False)
        except exceptions.AstroidBuildingException as e:
            for hook in self._failed_import_hooks:
                try:
                    return hook(modname)
                except exceptions.AstroidBuildingException:
                    pass
            raise e
        finally:
            os.chdir(old_cwd)

    def zip_import_data(self, filepath):
        if zipimport is None:
            return None
        from astroid.builder import AstroidBuilder
        builder = AstroidBuilder(self)
        for ext in ('.zip', '.egg'):
            try:
                eggpath, resource = filepath.rsplit(ext + os.path.sep, 1)
            except ValueError:
                continue
            try:
                importer = zipimport.zipimporter(eggpath + ext)
                zmodname = resource.replace(os.path.sep, '.')
                if importer.is_package(resource):
                    zmodname = zmodname + '.__init__'
                module = builder.string_build(importer.get_source(resource),
                                              zmodname, filepath)
                return module
            except Exception: # pylint: disable=broad-except
                continue
        return None

    def file_from_module_name(self, modname, contextfile):
        # pylint: disable=redefined-variable-type
        try:
            value = self._mod_file_cache[(modname, contextfile)]
        except KeyError:
            try:
                value = modutils.file_info_from_modpath(
                    modname.split('.'), context_file=contextfile)
            except ImportError as ex:
                msg = 'Unable to load module %s (%s)' % (modname, ex)
                value = exceptions.AstroidBuildingException(msg)
            self._mod_file_cache[(modname, contextfile)] = value
        if isinstance(value, exceptions.AstroidBuildingException):
            raise value
        return value

    def ast_from_module(self, module, modname=None):
        """given an imported module, return the astroid object"""
        modname = modname or module.__name__
        if modname in self.astroid_cache:
            return self.astroid_cache[modname]
        try:
            # some builtin modules don't have __file__ attribute
            filepath = module.__file__
            if modutils.is_python_source(filepath):
                return self.ast_from_file(filepath, modname)
        except AttributeError:
            pass
        from astroid.builder import AstroidBuilder
        return AstroidBuilder(self).module_build(module, modname)

    def ast_from_class(self, klass, modname=None):
        """get astroid for the given class"""
        if modname is None:
            try:
                modname = klass.__module__
            except AttributeError:
                msg = 'Unable to get module for class %s' % safe_repr(klass)
                raise exceptions.AstroidBuildingException(msg)
        modastroid = self.ast_from_module_name(modname)
        return modastroid.getattr(klass.__name__)[0] # XXX

    def infer_ast_from_something(self, obj, context=None):
        """infer astroid for the given class"""
        if hasattr(obj, '__class__') and not isinstance(obj, type):
            klass = obj.__class__
        else:
            klass = obj
        try:
            modname = klass.__module__
        except AttributeError:
            msg = 'Unable to get module for %s' % safe_repr(klass)
            raise exceptions.AstroidBuildingException(msg)
        except Exception as ex:
            msg = ('Unexpected error while retrieving module for %s: %s'
                   % (safe_repr(klass), ex))
            raise exceptions.AstroidBuildingException(msg)
        try:
            name = klass.__name__
        except AttributeError:
            msg = 'Unable to get name for %s' % safe_repr(klass)
            raise exceptions.AstroidBuildingException(msg)
        except Exception as ex:
            exc = ('Unexpected error while retrieving name for %s: %s'
                   % (safe_repr(klass), ex))
            raise exceptions.AstroidBuildingException(exc)
        # take care, on living object __module__ is regularly wrong :(
        modastroid = self.ast_from_module_name(modname)
        if klass is obj:
            for inferred in modastroid.igetattr(name, context):
                yield inferred
        else:
            for inferred in modastroid.igetattr(name, context):
                yield inferred.instantiate_class()

    def register_failed_import_hook(self, hook):
        """Registers a hook to resolve imports that cannot be found otherwise.

        `hook` must be a function that accepts a single argument `modname` which
        contains the name of the module or package that could not be imported.
        If `hook` can resolve the import, must return a node of type `astroid.Module`,
        otherwise, it must raise `AstroidBuildingException`.
        """
        self._failed_import_hooks.append(hook)

    def cache_module(self, module):
        """Cache a module if no module with the same name is known yet."""
        self.astroid_cache.setdefault(module.name, module)

    def clear_cache(self, astroid_builtin=None):
        # XXX clear transforms
        self.astroid_cache.clear()
        # force bootstrap again, else we may ends up with cache inconsistency
        # between the manager and CONST_PROXY, making
        # unittest_lookup.LookupTC.test_builtin_lookup fail depending on the
        # test order
        import astroid.raw_building
        astroid.raw_building._astroid_bootstrapping(
            astroid_builtin=astroid_builtin)
