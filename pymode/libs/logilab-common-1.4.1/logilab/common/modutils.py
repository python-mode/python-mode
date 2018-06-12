# -*- coding: utf-8 -*-
# copyright 2003-2013 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
# contact http://www.logilab.fr/ -- mailto:contact@logilab.fr
#
# This file is part of logilab-common.
#
# logilab-common is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 2.1 of the License, or (at your option) any
# later version.
#
# logilab-common is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with logilab-common.  If not, see <http://www.gnu.org/licenses/>.
"""Python modules manipulation utility functions.

:type PY_SOURCE_EXTS: tuple(str)
:var PY_SOURCE_EXTS: list of possible python source file extension

:type STD_LIB_DIR: str
:var STD_LIB_DIR: directory where standard modules are located

:type BUILTIN_MODULES: dict
:var BUILTIN_MODULES: dictionary with builtin module names as key
"""

__docformat__ = "restructuredtext en"

import sys
import os
from os.path import (splitext, join, abspath, isdir, dirname, exists,
                     basename, expanduser, normcase, realpath)
from imp import find_module, load_module, C_BUILTIN, PY_COMPILED, PKG_DIRECTORY
from distutils.sysconfig import get_config_var, get_python_lib, get_python_version
from distutils.errors import DistutilsPlatformError

from six import PY3
from six.moves import map, range

try:
    import zipimport
except ImportError:
    zipimport = None

ZIPFILE = object()

from logilab.common import STD_BLACKLIST, _handle_blacklist
from logilab.common.deprecation import deprecated

# Notes about STD_LIB_DIR
# Consider arch-specific installation for STD_LIB_DIR definition
# :mod:`distutils.sysconfig` contains to much hardcoded values to rely on
#
# :see: `Problems with /usr/lib64 builds <http://bugs.python.org/issue1294959>`_
# :see: `FHS <http://www.pathname.com/fhs/pub/fhs-2.3.html#LIBLTQUALGTALTERNATEFORMATESSENTIAL>`_
if sys.platform.startswith('win'):
    PY_SOURCE_EXTS = ('py', 'pyw')
    PY_COMPILED_EXTS = ('dll', 'pyd')
else:
    PY_SOURCE_EXTS = ('py',)
    PY_COMPILED_EXTS = ('so',)

try:
    STD_LIB_DIR = get_python_lib(standard_lib=True)
# get_python_lib(standard_lib=1) is not available on pypy, set STD_LIB_DIR to
# non-valid path, see https://bugs.pypy.org/issue1164
except DistutilsPlatformError:
    STD_LIB_DIR = '//'

EXT_LIB_DIR = get_python_lib()

BUILTIN_MODULES = dict.fromkeys(sys.builtin_module_names, True)


class NoSourceFile(Exception):
    """exception raised when we are not able to get a python
    source file for a precompiled file
    """

class LazyObject(object):
    def __init__(self, module, obj):
        self.module = module
        self.obj = obj
        self._imported = None

    def _getobj(self):
        if self._imported is None:
           self._imported = getattr(load_module_from_name(self.module),
                                    self.obj)
        return self._imported

    def __getattribute__(self, attr):
        try:
            return super(LazyObject, self).__getattribute__(attr)
        except AttributeError as ex:
            return getattr(self._getobj(), attr)

    def __call__(self, *args, **kwargs):
        return self._getobj()(*args, **kwargs)


def load_module_from_name(dotted_name, path=None, use_sys=True):
    """Load a Python module from its name.

    :type dotted_name: str
    :param dotted_name: python name of a module or package

    :type path: list or None
    :param path:
      optional list of path where the module or package should be
      searched (use sys.path if nothing or None is given)

    :type use_sys: bool
    :param use_sys:
      boolean indicating whether the sys.modules dictionary should be
      used or not


    :raise ImportError: if the module or package is not found

    :rtype: module
    :return: the loaded module
    """
    return load_module_from_modpath(dotted_name.split('.'), path, use_sys)


def load_module_from_modpath(parts, path=None, use_sys=True):
    """Load a python module from its splitted name.

    :type parts: list(str) or tuple(str)
    :param parts:
      python name of a module or package splitted on '.'

    :type path: list or None
    :param path:
      optional list of path where the module or package should be
      searched (use sys.path if nothing or None is given)

    :type use_sys: bool
    :param use_sys:
      boolean indicating whether the sys.modules dictionary should be used or not

    :raise ImportError: if the module or package is not found

    :rtype: module
    :return: the loaded module
    """
    if use_sys:
        try:
            return sys.modules['.'.join(parts)]
        except KeyError:
            pass
    modpath = []
    prevmodule = None
    for part in parts:
        modpath.append(part)
        curname = '.'.join(modpath)
        module = None
        if len(modpath) != len(parts):
            # even with use_sys=False, should try to get outer packages from sys.modules
            module = sys.modules.get(curname)
        elif use_sys:
            # because it may have been indirectly loaded through a parent
            module = sys.modules.get(curname)
        if module is None:
            mp_file, mp_filename, mp_desc = find_module(part, path)
            try:
                module = load_module(curname, mp_file, mp_filename, mp_desc)
            finally:
                if mp_file is not None:
                    mp_file.close()
        if prevmodule:
            setattr(prevmodule, part, module)
        _file = getattr(module, '__file__', '')
        prevmodule = module
        if not _file and _is_namespace(curname):
            continue
        if not _file and len(modpath) != len(parts):
            raise ImportError('no module in %s' % '.'.join(parts[len(modpath):]) )
        path = [dirname( _file )]
    return module


def load_module_from_file(filepath, path=None, use_sys=True, extrapath=None):
    """Load a Python module from it's path.

    :type filepath: str
    :param filepath: path to the python module or package

    :type path: list or None
    :param path:
      optional list of path where the module or package should be
      searched (use sys.path if nothing or None is given)

    :type use_sys: bool
    :param use_sys:
      boolean indicating whether the sys.modules dictionary should be
      used or not


    :raise ImportError: if the module or package is not found

    :rtype: module
    :return: the loaded module
    """
    modpath = modpath_from_file(filepath, extrapath)
    return load_module_from_modpath(modpath, path, use_sys)


def _check_init(path, mod_path):
    """check there are some __init__.py all along the way"""
    modpath = []
    for part in mod_path:
        modpath.append(part)
        path = join(path, part)
        if not _is_namespace('.'.join(modpath)) and not _has_init(path):
            return False
    return True


def _canonicalize_path(path):
    return realpath(expanduser(path))


def _path_from_filename(filename):
    if PY3:
        return filename
    else:
        if filename.endswith(".pyc"):
            return filename[:-1]
        return filename


@deprecated('you should avoid using modpath_from_file()')
def modpath_from_file(filename, extrapath=None):
    """DEPRECATED: doens't play well with symlinks and sys.meta_path

    Given a file path return the corresponding splitted module's name
    (i.e name of a module or package splitted on '.')

    :type filename: str
    :param filename: file's path for which we want the module's name

    :type extrapath: dict
    :param extrapath:
      optional extra search path, with path as key and package name for the path
      as value. This is usually useful to handle package splitted in multiple
      directories using __path__ trick.


    :raise ImportError:
      if the corresponding module's name has not been found

    :rtype: list(str)
    :return: the corresponding splitted module's name
    """
    filename = _path_from_filename(filename)
    filename = _canonicalize_path(filename)
    base = os.path.splitext(filename)[0]

    if extrapath is not None:
        for path_ in map(_canonicalize_path, extrapath):
            path = abspath(path_)
            if path and normcase(base[:len(path)]) == normcase(path):
                submodpath = [pkg for pkg in base[len(path):].split(os.sep)
                              if pkg]
                if _check_init(path, submodpath[:-1]):
                    return extrapath[path_].split('.') + submodpath

    for path in map(_canonicalize_path, sys.path):
        if path and normcase(base).startswith(path):
            modpath = [pkg for pkg in base[len(path):].split(os.sep) if pkg]
            if _check_init(path, modpath[:-1]):
                return modpath

    raise ImportError('Unable to find module for %s in %s' % (
        filename, ', \n'.join(sys.path)))


def file_from_modpath(modpath, path=None, context_file=None):
    """given a mod path (i.e. splitted module / package name), return the
    corresponding file, giving priority to source file over precompiled
    file if it exists

    :type modpath: list or tuple
    :param modpath:
      splitted module's name (i.e name of a module or package splitted
      on '.')
      (this means explicit relative imports that start with dots have
      empty strings in this list!)

    :type path: list or None
    :param path:
      optional list of path where the module or package should be
      searched (use sys.path if nothing or None is given)

    :type context_file: str or None
    :param context_file:
      context file to consider, necessary if the identifier has been
      introduced using a relative import unresolvable in the actual
      context (i.e. modutils)

    :raise ImportError: if there is no such module in the directory

    :rtype: str or None
    :return:
      the path to the module's file or None if it's an integrated
      builtin module such as 'sys'
    """
    if context_file is not None:
        context = dirname(context_file)
    else:
        context = context_file
    if modpath[0] == 'xml':
        # handle _xmlplus
        try:
            return _file_from_modpath(['_xmlplus'] + modpath[1:], path, context)
        except ImportError:
            return _file_from_modpath(modpath, path, context)
    elif modpath == ['os', 'path']:
        # FIXME: currently ignoring search_path...
        return os.path.__file__
    return _file_from_modpath(modpath, path, context)



def get_module_part(dotted_name, context_file=None):
    """given a dotted name return the module part of the name :

    >>> get_module_part('logilab.common.modutils.get_module_part')
    'logilab.common.modutils'

    :type dotted_name: str
    :param dotted_name: full name of the identifier we are interested in

    :type context_file: str or None
    :param context_file:
      context file to consider, necessary if the identifier has been
      introduced using a relative import unresolvable in the actual
      context (i.e. modutils)


    :raise ImportError: if there is no such module in the directory

    :rtype: str or None
    :return:
      the module part of the name or None if we have not been able at
      all to import the given name

    XXX: deprecated, since it doesn't handle package precedence over module
    (see #10066)
    """
    # os.path trick
    if dotted_name.startswith('os.path'):
        return 'os.path'
    parts = dotted_name.split('.')
    if context_file is not None:
        # first check for builtin module which won't be considered latter
        # in that case (path != None)
        if parts[0] in BUILTIN_MODULES:
            if len(parts) > 2:
                raise ImportError(dotted_name)
            return parts[0]
        # don't use += or insert, we want a new list to be created !
    path = None
    starti = 0
    if parts[0] == '':
        assert context_file is not None, \
                'explicit relative import, but no context_file?'
        path = [] # prevent resolving the import non-relatively
        starti = 1
    while parts[starti] == '': # for all further dots: change context
        starti += 1
        context_file = dirname(context_file)
    for i in range(starti, len(parts)):
        try:
            file_from_modpath(parts[starti:i+1],
                    path=path, context_file=context_file)
        except ImportError:
            if not i >= max(1, len(parts) - 2):
                raise
            return '.'.join(parts[:i])
    return dotted_name


def get_modules(package, src_directory, blacklist=STD_BLACKLIST):
    """given a package directory return a list of all available python
    modules in the package and its subpackages

    :type package: str
    :param package: the python name for the package

    :type src_directory: str
    :param src_directory:
      path of the directory corresponding to the package

    :type blacklist: list or tuple
    :param blacklist:
      optional list of files or directory to ignore, default to
      the value of `logilab.common.STD_BLACKLIST`

    :rtype: list
    :return:
      the list of all available python modules in the package and its
      subpackages
    """
    modules = []
    for directory, dirnames, filenames in os.walk(src_directory):
        _handle_blacklist(blacklist, dirnames, filenames)
        # check for __init__.py
        if not '__init__.py' in filenames:
            dirnames[:] = ()
            continue
        if directory != src_directory:
            dir_package = directory[len(src_directory):].replace(os.sep, '.')
            modules.append(package + dir_package)
        for filename in filenames:
            if _is_python_file(filename) and filename != '__init__.py':
                src = join(directory, filename)
                module = package + src[len(src_directory):-3]
                modules.append(module.replace(os.sep, '.'))
    return modules



def get_module_files(src_directory, blacklist=STD_BLACKLIST):
    """given a package directory return a list of all available python
    module's files in the package and its subpackages

    :type src_directory: str
    :param src_directory:
      path of the directory corresponding to the package

    :type blacklist: list or tuple
    :param blacklist:
      optional list of files or directory to ignore, default to the value of
      `logilab.common.STD_BLACKLIST`

    :rtype: list
    :return:
      the list of all available python module's files in the package and
      its subpackages
    """
    files = []
    for directory, dirnames, filenames in os.walk(src_directory):
        _handle_blacklist(blacklist, dirnames, filenames)
        # check for __init__.py
        if not '__init__.py' in filenames:
            dirnames[:] = ()
            continue
        for filename in filenames:
            if _is_python_file(filename):
                src = join(directory, filename)
                files.append(src)
    return files


def get_source_file(filename, include_no_ext=False):
    """given a python module's file name return the matching source file
    name (the filename will be returned identically if it's a already an
    absolute path to a python source file...)

    :type filename: str
    :param filename: python module's file name


    :raise NoSourceFile: if no source file exists on the file system

    :rtype: str
    :return: the absolute path of the source file if it exists
    """
    base, orig_ext = splitext(abspath(filename))
    for ext in PY_SOURCE_EXTS:
        source_path = '%s.%s' % (base, ext)
        if exists(source_path):
            return source_path
    if include_no_ext and not orig_ext and exists(base):
        return base
    raise NoSourceFile(filename)


def cleanup_sys_modules(directories):
    """remove submodules of `directories` from `sys.modules`"""
    cleaned = []
    for modname, module in list(sys.modules.items()):
        modfile = getattr(module, '__file__', None)
        if modfile:
            for directory in directories:
                if modfile.startswith(directory):
                    cleaned.append(modname)
                    del sys.modules[modname]
                    break
    return cleaned


def clean_sys_modules(names):
    """remove submodules starting with name from `names` from `sys.modules`"""
    cleaned = set()
    for modname in list(sys.modules):
        for name in names:
            if modname.startswith(name):
                del sys.modules[modname]
                cleaned.add(modname)
                break
    return cleaned


def is_python_source(filename):
    """
    rtype: bool
    return: True if the filename is a python source file
    """
    return splitext(filename)[1][1:] in PY_SOURCE_EXTS


def is_standard_module(modname, std_path=(STD_LIB_DIR,)):
    """try to guess if a module is a standard python module (by default,
    see `std_path` parameter's description)

    :type modname: str
    :param modname: name of the module we are interested in

    :type std_path: list(str) or tuple(str)
    :param std_path: list of path considered as standard


    :rtype: bool
    :return:
      true if the module:
      - is located on the path listed in one of the directory in `std_path`
      - is a built-in module

    Note: this function is known to return wrong values when inside virtualenv.
    See https://www.logilab.org/ticket/294756.
    """
    modname = modname.split('.')[0]
    try:
        filename = file_from_modpath([modname])
    except ImportError as ex:
        # import failed, i'm probably not so wrong by supposing it's
        # not standard...
        return False
    # modules which are not living in a file are considered standard
    # (sys and __builtin__ for instance)
    if filename is None:
        # we assume there are no namespaces in stdlib
        return not _is_namespace(modname)
    filename = abspath(filename)
    if filename.startswith(EXT_LIB_DIR):
        return False
    for path in std_path:
        if filename.startswith(abspath(path)):
            return True
    return False



def is_relative(modname, from_file):
    """return true if the given module name is relative to the given
    file name

    :type modname: str
    :param modname: name of the module we are interested in

    :type from_file: str
    :param from_file:
      path of the module from which modname has been imported

    :rtype: bool
    :return:
      true if the module has been imported relatively to `from_file`
    """
    if not isdir(from_file):
        from_file = dirname(from_file)
    if from_file in sys.path:
        return False
    try:
        find_module(modname.split('.')[0], [from_file])
        return True
    except ImportError:
        return False


# internal only functions #####################################################

def _file_from_modpath(modpath, path=None, context=None):
    """given a mod path (i.e. splitted module / package name), return the
    corresponding file

    this function is used internally, see `file_from_modpath`'s
    documentation for more information
    """
    assert len(modpath) > 0
    if context is not None:
        try:
            mtype, mp_filename = _module_file(modpath, [context])
        except ImportError:
            mtype, mp_filename = _module_file(modpath, path)
    else:
        mtype, mp_filename = _module_file(modpath, path)
    if mtype == PY_COMPILED:
        try:
            return get_source_file(mp_filename)
        except NoSourceFile:
            return mp_filename
    elif mtype == C_BUILTIN:
        # integrated builtin module
        return None
    elif mtype == PKG_DIRECTORY:
        mp_filename = _has_init(mp_filename)
    return mp_filename

def _search_zip(modpath, pic):
    for filepath, importer in pic.items():
        if importer is not None:
            if importer.find_module(modpath[0]):
                if not importer.find_module('/'.join(modpath)):
                    raise ImportError('No module named %s in %s/%s' % (
                        '.'.join(modpath[1:]), filepath, modpath))
                return ZIPFILE, abspath(filepath) + '/' + '/'.join(modpath), filepath
    raise ImportError('No module named %s' % '.'.join(modpath))

try:
    import pkg_resources
except ImportError:
    pkg_resources = None


def _is_namespace(modname):
    return (pkg_resources is not None
            and modname in pkg_resources._namespace_packages)


def _module_file(modpath, path=None):
    """get a module type / file path

    :type modpath: list or tuple
    :param modpath:
      splitted module's name (i.e name of a module or package splitted
      on '.'), with leading empty strings for explicit relative import

    :type path: list or None
    :param path:
      optional list of path where the module or package should be
      searched (use sys.path if nothing or None is given)


    :rtype: tuple(int, str)
    :return: the module type flag and the file path for a module
    """
    # egg support compat
    try:
        pic = sys.path_importer_cache
        _path = (path is None and sys.path or path)
        for __path in _path:
            if not __path in pic:
                try:
                    pic[__path] = zipimport.zipimporter(__path)
                except zipimport.ZipImportError:
                    pic[__path] = None
        checkeggs = True
    except AttributeError:
        checkeggs = False
    # pkg_resources support (aka setuptools namespace packages)
    if (_is_namespace(modpath[0]) and modpath[0] in sys.modules):
        # setuptools has added into sys.modules a module object with proper
        # __path__, get back information from there
        module = sys.modules[modpath.pop(0)]
        # use list() to protect against _NamespacePath instance we get with python 3, which
        # find_module later doesn't like
        path = list(module.__path__)
        if not modpath:
            return C_BUILTIN, None
    imported = []
    while modpath:
        modname = modpath[0]
        # take care to changes in find_module implementation wrt builtin modules
        #
        # Python 2.6.6 (r266:84292, Sep 11 2012, 08:34:23)
        # >>> imp.find_module('posix')
        # (None, 'posix', ('', '', 6))
        #
        # Python 3.3.1 (default, Apr 26 2013, 12:08:46)
        # >>> imp.find_module('posix')
        # (None, None, ('', '', 6))
        try:
            _, mp_filename, mp_desc = find_module(modname, path)
        except ImportError:
            if checkeggs:
                return _search_zip(modpath, pic)[:2]
            raise
        else:
            if checkeggs and mp_filename:
                fullabspath = [abspath(x) for x in _path]
                try:
                    pathindex = fullabspath.index(dirname(abspath(mp_filename)))
                    emtype, emp_filename, zippath = _search_zip(modpath, pic)
                    if pathindex > _path.index(zippath):
                        # an egg takes priority
                        return emtype, emp_filename
                except ValueError:
                    # XXX not in _path
                    pass
                except ImportError:
                    pass
                checkeggs = False
        imported.append(modpath.pop(0))
        mtype = mp_desc[2]
        if modpath:
            if mtype != PKG_DIRECTORY:
                raise ImportError('No module %s in %s' % ('.'.join(modpath),
                                                          '.'.join(imported)))
            # XXX guess if package is using pkgutil.extend_path by looking for
            # those keywords in the first four Kbytes
            try:
                with open(join(mp_filename, '__init__.py')) as stream:
                    data = stream.read(4096)
            except IOError:
                path = [mp_filename]
            else:
                if 'pkgutil' in data and 'extend_path' in data:
                    # extend_path is called, search sys.path for module/packages
                    # of this name see pkgutil.extend_path documentation
                    path = [join(p, *imported) for p in sys.path
                            if isdir(join(p, *imported))]
                else:
                    path = [mp_filename]
    return mtype, mp_filename

def _is_python_file(filename):
    """return true if the given filename should be considered as a python file

    .pyc and .pyo are ignored
    """
    for ext in ('.py', '.so', '.pyd', '.pyw'):
        if filename.endswith(ext):
            return True
    return False


def _has_init(directory):
    """if the given directory has a valid __init__ file, return its path,
    else return None
    """
    mod_or_pack = join(directory, '__init__')
    for ext in PY_SOURCE_EXTS + ('pyc', 'pyo'):
        if exists(mod_or_pack + '.' + ext):
            return mod_or_pack + '.' + ext
    return None
