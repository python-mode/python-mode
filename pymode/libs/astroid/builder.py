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

__docformat__ = "restructuredtext en"

import sys
from os.path import splitext, basename, exists, abspath

from astroid.exceptions import AstroidBuildingException, InferenceError
from astroid.raw_building import InspectBuilder
from astroid.rebuilder import TreeRebuilder
from astroid.manager import AstroidManager
from astroid.bases import YES, Instance
from astroid.modutils import modpath_from_file

from _ast import PyCF_ONLY_AST
def parse(string):
    return compile(string, "<string>", 'exec', PyCF_ONLY_AST)

if sys.version_info >= (3, 0):
    from tokenize import detect_encoding

    def open_source_file(filename):
        with open(filename, 'rb') as byte_stream:
            encoding = detect_encoding(byte_stream.readline)[0]
        stream = open(filename, 'r', newline=None, encoding=encoding)
        try:
            data = stream.read()
        except UnicodeError: # wrong encodingg
            # detect_encoding returns utf-8 if no encoding specified
            msg = 'Wrong (%s) or no encoding specified' % encoding
            raise AstroidBuildingException(msg)
        return stream, encoding, data

else:
    import re

    _ENCODING_RGX = re.compile(r"\s*#+.*coding[:=]\s*([-\w.]+)")

    def _guess_encoding(string):
        """get encoding from a python file as string or return None if not found
        """
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

# ast NG builder ##############################################################

MANAGER = AstroidManager()

class AstroidBuilder(InspectBuilder):
    """provide astroid building methods"""

    def __init__(self, manager=None):
        InspectBuilder.__init__(self)
        self._manager = manager or MANAGER

    def module_build(self, module, modname=None):
        """build an astroid from a living module instance
        """
        node = None
        path = getattr(module, '__file__', None)
        if path is not None:
            path_, ext = splitext(module.__file__)
            if ext in ('.py', '.pyc', '.pyo') and exists(path_ + '.py'):
                node = self.file_build(path_ + '.py', modname)
        if node is None:
            # this is a built-in module
            # get a partial representation by introspection
            node = self.inspect_build(module, modname=modname, path=path)
            # we have to handle transformation by ourselves since the rebuilder
            # isn't called for builtin nodes
            #
            # XXX it's then only called for Module nodes, not for underlying
            # nodes
            node = self._manager.transform(node)
        return node

    def file_build(self, path, modname=None):
        """build astroid from a source code file (i.e. from an ast)

        path is expected to be a python source file
        """
        try:
            stream, encoding, data = open_source_file(path)
        except IOError as exc:
            msg = 'Unable to load file %r (%s)' % (path, exc)
            raise AstroidBuildingException(msg)
        except SyntaxError as exc: # py3k encoding specification error
            raise AstroidBuildingException(exc)
        except LookupError as exc: # unknown encoding
            raise AstroidBuildingException(exc)
        with stream:
            # get module name if necessary
            if modname is None:
                try:
                    modname = '.'.join(modpath_from_file(path))
                except ImportError:
                    modname = splitext(basename(path))[0]
            # build astroid representation
            module = self._data_build(data, modname, path)
            return self._post_build(module, encoding)

    def string_build(self, data, modname='', path=None):
        """build astroid from source code string and return rebuilded astroid"""
        module = self._data_build(data, modname, path)
        module.file_bytes = data.encode('utf-8')
        return self._post_build(module, 'utf-8')

    def _post_build(self, module, encoding):
        """handles encoding and delayed nodes
        after a module has been built
        """
        module.file_encoding = encoding
        self._manager.cache_module(module)
        # post tree building steps after we stored the module in the cache:
        for from_node in module._from_nodes:
            if from_node.modname == '__future__':
                for symbol, _ in from_node.names:
                    module.future_imports.add(symbol)
            self.add_from_names_to_locals(from_node)
        # handle delayed assattr nodes
        for delayed in module._delayed_assattr:
            self.delayed_assattr(delayed)
        return module

    def _data_build(self, data, modname, path):
        """build tree node from data and add some informations"""
        # this method could be wrapped with a pickle/cache function
        try:
            node = parse(data + '\n')
        except TypeError as exc:
            raise AstroidBuildingException(exc)
        if path is not None:
            node_file = abspath(path)
        else:
            node_file = '<?>'
        if modname.endswith('.__init__'):
            modname = modname[:-9]
            package = True
        else:
            package = path and path.find('__init__.py') > -1 or False
        rebuilder = TreeRebuilder(self._manager)
        module = rebuilder.visit_module(node, modname, node_file, package)
        module._from_nodes = rebuilder._from_nodes
        module._delayed_assattr = rebuilder._delayed_assattr
        return module

    def add_from_names_to_locals(self, node):
        """store imported names to the locals;
        resort the locals if coming from a delayed node
        """

        _key_func = lambda node: node.fromlineno
        def sort_locals(my_list):
            my_list.sort(key=_key_func)
        for (name, asname) in node.names:
            if name == '*':
                try:
                    imported = node.do_import_module()
                except InferenceError:
                    continue
                for name in imported.wildcard_import_names():
                    node.parent.set_local(name, node)
                    sort_locals(node.parent.scope().locals[name])
            else:
                node.parent.set_local(asname or name, node)
                sort_locals(node.parent.scope().locals[asname or name])

    def delayed_assattr(self, node):
        """visit a AssAttr node -> add name to locals, handle members
        definition
        """
        try:
            frame = node.frame()
            for infered in node.expr.infer():
                if infered is YES:
                    continue
                try:
                    if infered.__class__ is Instance:
                        infered = infered._proxied
                        iattrs = infered.instance_attrs
                    elif isinstance(infered, Instance):
                        # Const, Tuple, ... we may be wrong, may be not, but
                        # anyway we don't want to pollute builtin's namespace
                        continue
                    elif infered.is_function:
                        iattrs = infered.instance_attrs
                    else:
                        iattrs = infered.locals
                except AttributeError:
                    # XXX log error
                    #import traceback
                    #traceback.print_exc()
                    continue
                values = iattrs.setdefault(node.attrname, [])
                if node in values:
                    continue
                # get assign in __init__ first XXX useful ?
                if frame.name == '__init__' and values and not \
                       values[0].frame().name == '__init__':
                    values.insert(0, node)
                else:
                    values.append(node)
        except InferenceError:
            pass

