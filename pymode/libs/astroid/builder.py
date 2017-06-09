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
"""The AstroidBuilder makes astroid from living object and / or from _ast

The builder is not thread safe and can't be used to parse different sources
at the same time.
"""
from __future__ import with_statement

import _ast
import os
import sys
import textwrap

from astroid import bases
from astroid import exceptions
from astroid import manager
from astroid import modutils
from astroid import raw_building
from astroid import rebuilder
from astroid import util


def _parse(string):
    return compile(string, "<string>", 'exec', _ast.PyCF_ONLY_AST)


if sys.version_info >= (3, 0):
    # pylint: disable=no-name-in-module; We don't understand flows yet.
    from tokenize import detect_encoding

    def open_source_file(filename):
        with open(filename, 'rb') as byte_stream:
            encoding = detect_encoding(byte_stream.readline)[0]
        stream = open(filename, 'r', newline=None, encoding=encoding)
        try:
            data = stream.read()
        except UnicodeError:  # wrong encoding
            # detect_encoding returns utf-8 if no encoding specified
            msg = 'Wrong (%s) or no encoding specified' % encoding
            raise exceptions.AstroidBuildingException(msg)
        return stream, encoding, data

else:
    import re

    _ENCODING_RGX = re.compile(r"\s*#+.*coding[:=]\s*([-\w.]+)")

    def _guess_encoding(string):
        """get encoding from a python file as string or return None if not found"""
        # check for UTF-8 byte-order mark
        if string.startswith('\xef\xbb\xbf'):
            return 'UTF-8'
        for line in string.split('\n', 2)[:2]:
            # check for encoding declaration
            match = _ENCODING_RGX.match(line)
            if match is not None:
                return match.group(1)

    def open_source_file(filename):
        """get data for parsing a file"""
        stream = open(filename, 'U')
        data = stream.read()
        encoding = _guess_encoding(data)
        return stream, encoding, data


MANAGER = manager.AstroidManager()


class AstroidBuilder(raw_building.InspectBuilder):
    """Class for building an astroid tree from source code or from a live module.

    The param *manager* specifies the manager class which should be used.
    If no manager is given, then the default one will be used. The
    param *apply_transforms* determines if the transforms should be
    applied after the tree was built from source or from a live object,
    by default being True.
    """

    def __init__(self, manager=None, apply_transforms=True):
        super(AstroidBuilder, self).__init__()
        self._manager = manager or MANAGER
        self._apply_transforms = apply_transforms

    def module_build(self, module, modname=None):
        """Build an astroid from a living module instance."""
        node = None
        path = getattr(module, '__file__', None)
        if path is not None:
            path_, ext = os.path.splitext(modutils._path_from_filename(path))
            if ext in ('.py', '.pyc', '.pyo') and os.path.exists(path_ + '.py'):
                node = self.file_build(path_ + '.py', modname)
        if node is None:
            # this is a built-in module
            # get a partial representation by introspection
            node = self.inspect_build(module, modname=modname, path=path)
            if self._apply_transforms:
                # We have to handle transformation by ourselves since the
                # rebuilder isn't called for builtin nodes
                node = self._manager.visit_transforms(node)
        return node

    def file_build(self, path, modname=None):
        """Build astroid from a source code file (i.e. from an ast)

        *path* is expected to be a python source file
        """
        try:
            stream, encoding, data = open_source_file(path)
        except IOError as exc:
            msg = 'Unable to load file %r (%s)' % (path, exc)
            raise exceptions.AstroidBuildingException(msg)
        except SyntaxError as exc:  # py3k encoding specification error
            raise exceptions.AstroidBuildingException(exc)
        except LookupError as exc:  # unknown encoding
            raise exceptions.AstroidBuildingException(exc)
        with stream:
            # get module name if necessary
            if modname is None:
                try:
                    modname = '.'.join(modutils.modpath_from_file(path))
                except ImportError:
                    modname = os.path.splitext(os.path.basename(path))[0]
            # build astroid representation
            module = self._data_build(data, modname, path)
            return self._post_build(module, encoding)

    def string_build(self, data, modname='', path=None):
        """Build astroid from source code string."""
        module = self._data_build(data, modname, path)
        module.source_code = data.encode('utf-8')
        return self._post_build(module, 'utf-8')

    def _post_build(self, module, encoding):
        """Handles encoding and delayed nodes after a module has been built"""
        module.file_encoding = encoding
        self._manager.cache_module(module)
        # post tree building steps after we stored the module in the cache:
        for from_node in module._import_from_nodes:
            if from_node.modname == '__future__':
                for symbol, _ in from_node.names:
                    module._future_imports.add(symbol)
            self.add_from_names_to_locals(from_node)
        # handle delayed assattr nodes
        for delayed in module._delayed_assattr:
            self.delayed_assattr(delayed)

        # Visit the transforms
        if self._apply_transforms:
            module = self._manager.visit_transforms(module)
        return module

    def _data_build(self, data, modname, path):
        """Build tree node from data and add some informations"""
        try:
            node = _parse(data + '\n')
        except (TypeError, ValueError, SyntaxError) as exc:
            raise exceptions.AstroidBuildingException(exc)
        if path is not None:
            node_file = os.path.abspath(path)
        else:
            node_file = '<?>'
        if modname.endswith('.__init__'):
            modname = modname[:-9]
            package = True
        else:
            package = path and path.find('__init__.py') > -1 or False
        builder = rebuilder.TreeRebuilder(self._manager)
        module = builder.visit_module(node, modname, node_file, package)
        module._import_from_nodes = builder._import_from_nodes
        module._delayed_assattr = builder._delayed_assattr
        return module

    def add_from_names_to_locals(self, node):
        """Store imported names to the locals

        Resort the locals if coming from a delayed node
        """
        _key_func = lambda node: node.fromlineno
        def sort_locals(my_list):
            my_list.sort(key=_key_func)

        for (name, asname) in node.names:
            if name == '*':
                try:
                    imported = node.do_import_module()
                except exceptions.InferenceError:
                    continue
                for name in imported._public_names():
                    node.parent.set_local(name, node)
                    sort_locals(node.parent.scope()._locals[name])
            else:
                node.parent.set_local(asname or name, node)
                sort_locals(node.parent.scope()._locals[asname or name])

    def delayed_assattr(self, node):
        """Visit a AssAttr node

        This adds name to locals and handle members definition.
        """
        try:
            frame = node.frame()
            for inferred in node.expr.infer():
                if inferred is util.YES:
                    continue
                try:
                    if inferred.__class__ is bases.Instance:
                        inferred = inferred._proxied
                        iattrs = inferred._instance_attrs
                    elif isinstance(inferred, bases.Instance):
                        # Const, Tuple, ... we may be wrong, may be not, but
                        # anyway we don't want to pollute builtin's namespace
                        continue
                    elif inferred.is_function:
                        iattrs = inferred._instance_attrs
                    else:
                        iattrs = inferred._locals
                except AttributeError:
                    # XXX log error
                    continue
                values = iattrs.setdefault(node.attrname, [])
                if node in values:
                    continue
                # get assign in __init__ first XXX useful ?
                if (frame.name == '__init__' and values and
                        not values[0].frame().name == '__init__'):
                    values.insert(0, node)
                else:
                    values.append(node)
        except exceptions.InferenceError:
            pass


def parse(code, module_name='', path=None, apply_transforms=True):
    """Parses a source string in order to obtain an astroid AST from it

    :param str code: The code for the module.
    :param str module_name: The name for the module, if any
    :param str path: The path for the module
    :param bool apply_transforms:
        Apply the transforms for the give code. Use it if you
        don't want the default transforms to be applied.
    """
    code = textwrap.dedent(code)
    builder = AstroidBuilder(manager=MANAGER,
                             apply_transforms=apply_transforms)
    return builder.string_build(code, modname=module_name, path=path)
