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
"""This module contains base classes and functions for the nodes and some
inference utils.
"""

__docformat__ = "restructuredtext en"

import sys
from contextlib import contextmanager

from logilab.common.decorators import cachedproperty

from astroid.exceptions import (InferenceError, AstroidError, NotFoundError,
                                UnresolvableName, UseInferenceDefault)


if sys.version_info >= (3, 0):
    BUILTINS = 'builtins'
else:
    BUILTINS = '__builtin__'


class Proxy(object):
    """a simple proxy object"""

    _proxied = None # proxied object may be set by class or by instance

    def __init__(self, proxied=None):
        if proxied is not None:
            self._proxied = proxied

    def __getattr__(self, name):
        if name == '_proxied':
            return getattr(self.__class__, '_proxied')
        if name in self.__dict__:
            return self.__dict__[name]
        return getattr(self._proxied, name)

    def infer(self, context=None):
        yield self


# Inference ##################################################################

class InferenceContext(object):
    __slots__ = ('path', 'lookupname', 'callcontext', 'boundnode', 'infered')

    def __init__(self, path=None, infered=None):
        self.path = path or set()
        self.lookupname = None
        self.callcontext = None
        self.boundnode = None
        self.infered = infered or {}

    def push(self, node):
        name = self.lookupname
        if (node, name) in self.path:
            raise StopIteration()
        self.path.add((node, name))

    def clone(self):
        # XXX copy lookupname/callcontext ?
        clone = InferenceContext(self.path, infered=self.infered)
        clone.callcontext = self.callcontext
        clone.boundnode = self.boundnode
        return clone

    def cache_generator(self, key, generator):
        results = []
        for result in generator:
            results.append(result)
            yield result

        self.infered[key] = tuple(results)
        return

    @contextmanager
    def restore_path(self):
        path = set(self.path)
        yield
        self.path = path

def copy_context(context):
    if context is not None:
        return context.clone()
    else:
        return InferenceContext()


def _infer_stmts(stmts, context, frame=None):
    """return an iterator on statements inferred by each statement in <stmts>
    """
    stmt = None
    infered = False
    if context is not None:
        name = context.lookupname
        context = context.clone()
    else:
        name = None
        context = InferenceContext()
    for stmt in stmts:
        if stmt is YES:
            yield stmt
            infered = True
            continue
        context.lookupname = stmt._infer_name(frame, name)
        try:
            for infered in stmt.infer(context):
                yield infered
                infered = True
        except UnresolvableName:
            continue
        except InferenceError:
            yield YES
            infered = True
    if not infered:
        raise InferenceError(str(stmt))


# special inference objects (e.g. may be returned as nodes by .infer()) #######

class _Yes(object):
    """a yes object"""
    def __repr__(self):
        return 'YES'
    def __getattribute__(self, name):
        if name == 'next':
            raise AttributeError('next method should not be called')
        if name.startswith('__') and name.endswith('__'):
            # to avoid inspection pb
            return super(_Yes, self).__getattribute__(name)
        return self
    def __call__(self, *args, **kwargs):
        return self


YES = _Yes()


class Instance(Proxy):
    """a special node representing a class instance"""
    def getattr(self, name, context=None, lookupclass=True):
        try:
            values = self._proxied.instance_attr(name, context)
        except NotFoundError:
            if name == '__class__':
                return [self._proxied]
            if lookupclass:
                # class attributes not available through the instance
                # unless they are explicitly defined
                if name in ('__name__', '__bases__', '__mro__', '__subclasses__'):
                    return self._proxied.local_attr(name)
                return self._proxied.getattr(name, context)
            raise NotFoundError(name)
        # since we've no context information, return matching class members as
        # well
        if lookupclass:
            try:
                return values + self._proxied.getattr(name, context)
            except NotFoundError:
                pass
        return values

    def igetattr(self, name, context=None):
        """inferred getattr"""
        if not context:
            context = InferenceContext()
        try:
            # avoid recursively inferring the same attr on the same class

            context.push((self._proxied, name))
            # XXX frame should be self._proxied, or not ?
            get_attr = self.getattr(name, context, lookupclass=False)
            return _infer_stmts(
                self._wrap_attr(get_attr, context),
                context,
                frame=self,
            )
        except NotFoundError:
            try:
                # fallback to class'igetattr since it has some logic to handle
                # descriptors
                return self._wrap_attr(self._proxied.igetattr(name, context),
                                       context)
            except NotFoundError:
                raise InferenceError(name)

    def _wrap_attr(self, attrs, context=None):
        """wrap bound methods of attrs in a InstanceMethod proxies"""
        for attr in attrs:
            if isinstance(attr, UnboundMethod):
                if BUILTINS + '.property' in attr.decoratornames():
                    for infered in attr.infer_call_result(self, context):
                        yield infered
                else:
                    yield BoundMethod(attr, self)
            else:
                yield attr

    def infer_call_result(self, caller, context=None):
        """infer what a class instance is returning when called"""
        infered = False
        for node in self._proxied.igetattr('__call__', context):
            if node is YES:
                continue
            for res in node.infer_call_result(caller, context):
                infered = True
                yield res
        if not infered:
            raise InferenceError()

    def __repr__(self):
        return '<Instance of %s.%s at 0x%s>' % (self._proxied.root().name,
                                                self._proxied.name,
                                                id(self))
    def __str__(self):
        return 'Instance of %s.%s' % (self._proxied.root().name,
                                      self._proxied.name)

    def callable(self):
        try:
            self._proxied.getattr('__call__')
            return True
        except NotFoundError:
            return False

    def pytype(self):
        return self._proxied.qname()

    def display_type(self):
        return 'Instance of'


class UnboundMethod(Proxy):
    """a special node representing a method not bound to an instance"""
    def __repr__(self):
        frame = self._proxied.parent.frame()
        return '<%s %s of %s at 0x%s' % (self.__class__.__name__,
                                         self._proxied.name,
                                         frame.qname(), id(self))

    def is_bound(self):
        return False

    def getattr(self, name, context=None):
        if name == 'im_func':
            return [self._proxied]
        return super(UnboundMethod, self).getattr(name, context)

    def igetattr(self, name, context=None):
        if name == 'im_func':
            return iter((self._proxied,))
        return super(UnboundMethod, self).igetattr(name, context)

    def infer_call_result(self, caller, context):
        # If we're unbound method __new__ of builtin object, the result is an
        # instance of the class given as first argument.
        if (self._proxied.name == '__new__' and
                self._proxied.parent.frame().qname() == '%s.object' % BUILTINS):
            infer = caller.args[0].infer() if caller.args else []
            return ((x is YES and x or Instance(x)) for x in infer)
        return self._proxied.infer_call_result(caller, context)


class BoundMethod(UnboundMethod):
    """a special node representing a method bound to an instance"""
    def __init__(self, proxy, bound):
        UnboundMethod.__init__(self, proxy)
        self.bound = bound

    def is_bound(self):
        return True

    def infer_call_result(self, caller, context):
        context = context.clone()
        context.boundnode = self.bound
        return self._proxied.infer_call_result(caller, context)


class Generator(Instance):
    """a special node representing a generator.

    Proxied class is set once for all in raw_building.
    """
    def callable(self):
        return False

    def pytype(self):
        return '%s.generator' % BUILTINS

    def display_type(self):
        return 'Generator'

    def __repr__(self):
        return '<Generator(%s) l.%s at 0x%s>' % (self._proxied.name, self.lineno, id(self))

    def __str__(self):
        return 'Generator(%s)' % (self._proxied.name)


# decorators ##################################################################

def path_wrapper(func):
    """return the given infer function wrapped to handle the path"""
    def wrapped(node, context=None, _func=func, **kwargs):
        """wrapper function handling context"""
        if context is None:
            context = InferenceContext()
        context.push(node)
        yielded = set()
        for res in _func(node, context, **kwargs):
            # unproxy only true instance, not const, tuple, dict...
            if res.__class__ is Instance:
                ares = res._proxied
            else:
                ares = res
            if not ares in yielded:
                yield res
                yielded.add(ares)
    return wrapped

def yes_if_nothing_infered(func):
    def wrapper(*args, **kwargs):
        infered = False
        for node in func(*args, **kwargs):
            infered = True
            yield node
        if not infered:
            yield YES
    return wrapper

def raise_if_nothing_infered(func):
    def wrapper(*args, **kwargs):
        infered = False
        for node in func(*args, **kwargs):
            infered = True
            yield node
        if not infered:
            raise InferenceError()
    return wrapper


# Node  ######################################################################

class NodeNG(object):
    """Base Class for all Astroid node classes.

    It represents a node of the new abstract syntax tree.
    """
    is_statement = False
    optional_assign = False # True  for For (and for Comprehension if py <3.0)
    is_function = False # True for Function nodes
    # attributes below are set by the builder module or by raw factories
    lineno = None
    fromlineno = None
    tolineno = None
    col_offset = None
    # parent node in the tree
    parent = None
    # attributes containing child node(s) redefined in most concrete classes:
    _astroid_fields = ()
    # instance specific inference function infer(node, context)
    _explicit_inference = None

    def infer(self, context=None, **kwargs):
        """main interface to the interface system, return a generator on infered
        values.

        If the instance has some explicit inference function set, it will be
        called instead of the default interface.
        """
        if self._explicit_inference is not None:
            # explicit_inference is not bound, give it self explicitly
            try:
                return self._explicit_inference(self, context, **kwargs)
            except UseInferenceDefault:
                pass

        if not context:
            return self._infer(context, **kwargs)

        key = (self, context.lookupname,
               context.callcontext, context.boundnode)
        if key in context.infered:
            return iter(context.infered[key])

        return context.cache_generator(key, self._infer(context, **kwargs))

    def _repr_name(self):
        """return self.name or self.attrname or '' for nice representation"""
        return getattr(self, 'name', getattr(self, 'attrname', ''))

    def __str__(self):
        return '%s(%s)' % (self.__class__.__name__, self._repr_name())

    def __repr__(self):
        return '<%s(%s) l.%s [%s] at 0x%x>' % (self.__class__.__name__,
                                               self._repr_name(),
                                               self.fromlineno,
                                               self.root().name,
                                               id(self))


    def accept(self, visitor):
        func = getattr(visitor, "visit_" + self.__class__.__name__.lower())
        return func(self)

    def get_children(self):
        for field in self._astroid_fields:
            attr = getattr(self, field)
            if attr is None:
                continue
            if isinstance(attr, (list, tuple)):
                for elt in attr:
                    yield elt
            else:
                yield attr

    def last_child(self):
        """an optimized version of list(get_children())[-1]"""
        for field in self._astroid_fields[::-1]:
            attr = getattr(self, field)
            if not attr: # None or empty listy / tuple
                continue
            if attr.__class__ in (list, tuple):
                return attr[-1]
            else:
                return attr
        return None

    def parent_of(self, node):
        """return true if i'm a parent of the given node"""
        parent = node.parent
        while parent is not None:
            if self is parent:
                return True
            parent = parent.parent
        return False

    def statement(self):
        """return the first parent node marked as statement node"""
        if self.is_statement:
            return self
        return self.parent.statement()

    def frame(self):
        """return the first parent frame node (i.e. Module, Function or Class)
        """
        return self.parent.frame()

    def scope(self):
        """return the first node defining a new scope (i.e. Module, Function,
        Class, Lambda but also GenExpr)
        """
        return self.parent.scope()

    def root(self):
        """return the root node of the tree, (i.e. a Module)"""
        if self.parent:
            return self.parent.root()
        return self

    def child_sequence(self, child):
        """search for the right sequence where the child lies in"""
        for field in self._astroid_fields:
            node_or_sequence = getattr(self, field)
            if node_or_sequence is child:
                return [node_or_sequence]
            # /!\ compiler.ast Nodes have an __iter__ walking over child nodes
            if isinstance(node_or_sequence, (tuple, list)) and child in node_or_sequence:
                return node_or_sequence
        else:
            msg = 'Could not find %s in %s\'s children'
            raise AstroidError(msg % (repr(child), repr(self)))

    def locate_child(self, child):
        """return a 2-uple (child attribute name, sequence or node)"""
        for field in self._astroid_fields:
            node_or_sequence = getattr(self, field)
            # /!\ compiler.ast Nodes have an __iter__ walking over child nodes
            if child is node_or_sequence:
                return field, child
            if isinstance(node_or_sequence, (tuple, list)) and child in node_or_sequence:
                return field, node_or_sequence
        msg = 'Could not find %s in %s\'s children'
        raise AstroidError(msg % (repr(child), repr(self)))
    # FIXME : should we merge child_sequence and locate_child ? locate_child
    # is only used in are_exclusive, child_sequence one time in pylint.

    def next_sibling(self):
        """return the next sibling statement"""
        return self.parent.next_sibling()

    def previous_sibling(self):
        """return the previous sibling statement"""
        return self.parent.previous_sibling()

    def nearest(self, nodes):
        """return the node which is the nearest before this one in the
        given list of nodes
        """
        myroot = self.root()
        mylineno = self.fromlineno
        nearest = None, 0
        for node in nodes:
            assert node.root() is myroot, \
                   'nodes %s and %s are not from the same module' % (self, node)
            lineno = node.fromlineno
            if node.fromlineno > mylineno:
                break
            if lineno > nearest[1]:
                nearest = node, lineno
        # FIXME: raise an exception if nearest is None ?
        return nearest[0]

    # these are lazy because they're relatively expensive to compute for every
    # single node, and they rarely get looked at

    @cachedproperty
    def fromlineno(self):
        if self.lineno is None:
            return self._fixed_source_line()
        else:
            return self.lineno

    @cachedproperty
    def tolineno(self):
        if not self._astroid_fields:
            # can't have children
            lastchild = None
        else:
            lastchild = self.last_child()
        if lastchild is None:
            return self.fromlineno
        else:
            return lastchild.tolineno

        # TODO / FIXME:
        assert self.fromlineno is not None, self
        assert self.tolineno is not None, self

    def _fixed_source_line(self):
        """return the line number where the given node appears

        we need this method since not all nodes have the lineno attribute
        correctly set...
        """
        line = self.lineno
        _node = self
        try:
            while line is None:
                _node = next(_node.get_children())
                line = _node.lineno
        except StopIteration:
            _node = self.parent
            while _node and line is None:
                line = _node.lineno
                _node = _node.parent
        return line

    def block_range(self, lineno):
        """handle block line numbers range for non block opening statements
        """
        return lineno, self.tolineno

    def set_local(self, name, stmt):
        """delegate to a scoped parent handling a locals dictionary"""
        self.parent.set_local(name, stmt)

    def nodes_of_class(self, klass, skip_klass=None):
        """return an iterator on nodes which are instance of the given class(es)

        klass may be a class object or a tuple of class objects
        """
        if isinstance(self, klass):
            yield self
        for child_node in self.get_children():
            if skip_klass is not None and isinstance(child_node, skip_klass):
                continue
            for matching in child_node.nodes_of_class(klass, skip_klass):
                yield matching

    def _infer_name(self, frame, name):
        # overridden for From, Import, Global, TryExcept and Arguments
        return None

    def _infer(self, context=None):
        """we don't know how to resolve a statement by default"""
        # this method is overridden by most concrete classes
        raise InferenceError(self.__class__.__name__)

    def infered(self):
        '''return list of infered values for a more simple inference usage'''
        return list(self.infer())

    def instanciate_class(self):
        """instanciate a node if it is a Class node, else return self"""
        return self

    def has_base(self, node):
        return False

    def callable(self):
        return False

    def eq(self, value):
        return False

    def as_string(self):
        from astroid.as_string import to_code
        return to_code(self)

    def repr_tree(self, ids=False):
        from astroid.as_string import dump
        return dump(self)


class Statement(NodeNG):
    """Statement node adding a few attributes"""
    is_statement = True

    def next_sibling(self):
        """return the next sibling statement"""
        stmts = self.parent.child_sequence(self)
        index = stmts.index(self)
        try:
            return stmts[index +1]
        except IndexError:
            pass

    def previous_sibling(self):
        """return the previous sibling statement"""
        stmts = self.parent.child_sequence(self)
        index = stmts.index(self)
        if index >= 1:
            return stmts[index -1]
