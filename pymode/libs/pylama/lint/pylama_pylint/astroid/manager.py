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

__docformat__ = "restructuredtext en"

import os
from os.path import dirname, join, isdir, exists

from logilab.common.modutils import NoSourceFile, is_python_source, \
     file_from_modpath, load_module_from_name, modpath_from_file, \
     get_module_files, get_source_file, zipimport
from logilab.common.configuration import OptionsProviderMixIn

from astroid.exceptions import AstroidBuildingException

def astroid_wrapper(func, modname):
    """wrapper to give to AstroidManager.project_from_files"""
    print 'parsing %s...' % modname
    try:
        return func(modname)
    except AstroidBuildingException, exc:
        print exc
    except Exception, exc:
        import traceback
        traceback.print_exc()

def _silent_no_wrap(func, modname):
    """silent wrapper that doesn't do anything; can be used for tests"""
    return func(modname)

def safe_repr(obj):
    try:
        return repr(obj)
    except:
        return '???'



class AstroidManager(OptionsProviderMixIn):
    """the astroid manager, responsible to build astroid from files
     or modules.

    Use the Borg pattern.
    """

    name = 'astroid loader'
    options = (("ignore",
                {'type' : "csv", 'metavar' : "<file>",
                 'dest' : "black_list", "default" : ('CVS',),
                 'help' : "add <file> (may be a directory) to the black list\
. It should be a base name, not a path. You may set this option multiple times\
."}),
               ("project",
                {'default': "No Name", 'type' : 'string', 'short': 'p',
                 'metavar' : '<project name>',
                 'help' : 'set the project name.'}),
               )
    brain = {}
    def __init__(self):
        self.__dict__ = AstroidManager.brain
        if not self.__dict__:
            OptionsProviderMixIn.__init__(self)
            self.load_defaults()
            # NOTE: cache entries are added by the [re]builder
            self.astroid_cache = {}
            self._mod_file_cache = {}
            self.transforms = {}

    def ast_from_file(self, filepath, modname=None, fallback=True, source=False):
        """given a module name, return the astroid object"""
        try:
            filepath = get_source_file(filepath, include_no_ext=True)
            source = True
        except NoSourceFile:
            pass
        if modname is None:
            try:
                modname = '.'.join(modpath_from_file(filepath))
            except ImportError:
                modname = filepath
        if modname in self.astroid_cache and self.astroid_cache[modname].file == filepath:
            return self.astroid_cache[modname]
        if source:
            from astroid.builder import AstroidBuilder
            return AstroidBuilder(self).file_build(filepath, modname)
        elif fallback and modname:
            return self.ast_from_module_name(modname)
        raise AstroidBuildingException('unable to get astroid for file %s' %
                                     filepath)

    def ast_from_module_name(self, modname, context_file=None):
        """given a module name, return the astroid object"""
        if modname in self.astroid_cache:
            return self.astroid_cache[modname]
        if modname == '__main__':
            from astroid.builder import AstroidBuilder
            return AstroidBuilder(self).string_build('', modname)
        old_cwd = os.getcwd()
        if context_file:
            os.chdir(dirname(context_file))
        try:
            filepath = self.file_from_module_name(modname, context_file)
            if filepath is not None and not is_python_source(filepath):
                module = self.zip_import_data(filepath)
                if module is not None:
                    return module
            if filepath is None or not is_python_source(filepath):
                try:
                    module = load_module_from_name(modname)
                except Exception, ex:
                    msg = 'Unable to load module %s (%s)' % (modname, ex)
                    raise AstroidBuildingException(msg)
                return self.ast_from_module(module, modname)
            return self.ast_from_file(filepath, modname, fallback=False)
        finally:
            os.chdir(old_cwd)

    def zip_import_data(self, filepath):
        if zipimport is None:
            return None
        from astroid.builder import AstroidBuilder
        builder = AstroidBuilder(self)
        for ext in ('.zip', '.egg'):
            try:
                eggpath, resource = filepath.rsplit(ext + '/', 1)
            except ValueError:
                continue
            try:
                importer = zipimport.zipimporter(eggpath + ext)
                zmodname = resource.replace('/', '.')
                if importer.is_package(resource):
                    zmodname =  zmodname + '.__init__'
                module = builder.string_build(importer.get_source(resource),
                                              zmodname, filepath)
                return module
            except:
                continue
        return None

    def file_from_module_name(self, modname, contextfile):
        try:
            value = self._mod_file_cache[(modname, contextfile)]
        except KeyError:
            try:
                value = file_from_modpath(modname.split('.'),
                                          context_file=contextfile)
            except ImportError, ex:
                msg = 'Unable to load module %s (%s)' % (modname, ex)
                value = AstroidBuildingException(msg)
            self._mod_file_cache[(modname, contextfile)] = value
        if isinstance(value, AstroidBuildingException):
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
            if is_python_source(filepath):
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
                raise AstroidBuildingException(
                    'Unable to get module for class %s' % safe_repr(klass))
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
            raise AstroidBuildingException(
                'Unable to get module for %s' % safe_repr(klass))
        except Exception, ex:
            raise AstroidBuildingException(
                'Unexpected error while retrieving module for %s: %s'
                % (safe_repr(klass), ex))
        try:
            name = klass.__name__
        except AttributeError:
            raise AstroidBuildingException(
                'Unable to get name for %s' % safe_repr(klass))
        except Exception, ex:
            raise AstroidBuildingException(
                'Unexpected error while retrieving name for %s: %s'
                % (safe_repr(klass), ex))
        # take care, on living object __module__ is regularly wrong :(
        modastroid = self.ast_from_module_name(modname)
        if klass is obj:
            for  infered in modastroid.igetattr(name, context):
                yield infered
        else:
            for infered in modastroid.igetattr(name, context):
                yield infered.instanciate_class()

    def project_from_files(self, files, func_wrapper=astroid_wrapper,
                           project_name=None, black_list=None):
        """return a Project from a list of files or modules"""
        # build the project representation
        project_name = project_name or self.config.project
        black_list = black_list or self.config.black_list
        project = Project(project_name)
        for something in files:
            if not exists(something):
                fpath = file_from_modpath(something.split('.'))
            elif isdir(something):
                fpath = join(something, '__init__.py')
            else:
                fpath = something
            astroid = func_wrapper(self.ast_from_file, fpath)
            if astroid is None:
                continue
            # XXX why is first file defining the project.path ?
            project.path = project.path or astroid.file
            project.add_module(astroid)
            base_name = astroid.name
            # recurse in package except if __init__ was explicitly given
            if astroid.package and something.find('__init__') == -1:
                # recurse on others packages / modules if this is a package
                for fpath in get_module_files(dirname(astroid.file),
                                              black_list):
                    astroid = func_wrapper(self.ast_from_file, fpath)
                    if astroid is None or astroid.name == base_name:
                        continue
                    project.add_module(astroid)
        return project

    def register_transform(self, node_class, transform, predicate=None):
        """Register `transform(node)` function to be applied on the given
        Astroid's `node_class` if `predicate` is None or return a true value
        when called with the node as argument.

        The transform function may return a value which is then used to
        substitute the original node in the tree.
        """
        self.transforms.setdefault(node_class, []).append( (transform, predicate) )

    def unregister_transform(self, node_class, transform, predicate=None):
        """Unregister the given transform."""
        self.transforms[node_class].remove( (transform, predicate) )

    def transform(self, node):
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
                        warn('node %s substitued multiple times' % node)
                    node = ret
        return node

    def cache_module(self, module):
        """Cache a module if no module with the same name is known yet."""
        self.astroid_cache.setdefault(module.name, module)


class Project(object):
    """a project handle a set of modules / packages"""
    def __init__(self, name=''):
        self.name = name
        self.path = None
        self.modules = []
        self.locals = {}
        self.__getitem__ = self.locals.__getitem__
        self.__iter__ = self.locals.__iter__
        self.values = self.locals.values
        self.keys = self.locals.keys
        self.items = self.locals.items

    def add_module(self, node):
        self.locals[node.name] = node
        self.modules.append(node)

    def get_module(self, name):
        return self.locals[name]

    def get_children(self):
        return self.modules

    def __repr__(self):
        return '<Project %r at %s (%s modules)>' % (self.name, id(self),
                                                    len(self.modules))


