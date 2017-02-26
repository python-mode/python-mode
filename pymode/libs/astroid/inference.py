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
"""this module contains a set of functions to handle inference on astroid trees
"""

from __future__ import print_function

from astroid import bases
from astroid import context as contextmod
from astroid import exceptions
from astroid import manager
from astroid import nodes
from astroid import protocols
from astroid import util


MANAGER = manager.AstroidManager()


# .infer method ###############################################################


def infer_end(self, context=None):
    """inference's end for node such as Module, ClassDef, FunctionDef,
    Const...

    """
    yield self
nodes.Module._infer = infer_end
nodes.ClassDef._infer = infer_end
nodes.FunctionDef._infer = infer_end
nodes.Lambda._infer = infer_end
nodes.Const._infer = infer_end
nodes.List._infer = infer_end
nodes.Tuple._infer = infer_end
nodes.Dict._infer = infer_end
nodes.Set._infer = infer_end

def _higher_function_scope(node):
    """ Search for the first function which encloses the given
    scope. This can be used for looking up in that function's
    scope, in case looking up in a lower scope for a particular
    name fails.

    :param node: A scope node.
    :returns:
        ``None``, if no parent function scope was found,
        otherwise an instance of :class:`astroid.scoped_nodes.Function`,
        which encloses the given node.
    """
    current = node
    while current.parent and not isinstance(current.parent, nodes.FunctionDef):
        current = current.parent
    if current and current.parent:
        return current.parent

def infer_name(self, context=None):
    """infer a Name: use name lookup rules"""
    frame, stmts = self.lookup(self.name)
    if not stmts:
        # Try to see if the name is enclosed in a nested function
        # and use the higher (first function) scope for searching.
        # TODO: should this be promoted to other nodes as well?
        parent_function = _higher_function_scope(self.scope())
        if parent_function:
            _, stmts = parent_function.lookup(self.name)

        if not stmts:
            raise exceptions.UnresolvableName(self.name)
    context = context.clone()
    context.lookupname = self.name
    return bases._infer_stmts(stmts, context, frame)
nodes.Name._infer = bases.path_wrapper(infer_name)
nodes.AssignName.infer_lhs = infer_name # won't work with a path wrapper


@bases.path_wrapper
@bases.raise_if_nothing_inferred
def infer_call(self, context=None):
    """infer a Call node by trying to guess what the function returns"""
    callcontext = context.clone()
    callcontext.callcontext = contextmod.CallContext(args=self.args,
                                                     keywords=self.keywords)
    callcontext.boundnode = None
    for callee in self.func.infer(context):
        if callee is util.YES:
            yield callee
            continue
        try:
            if hasattr(callee, 'infer_call_result'):
                for inferred in callee.infer_call_result(self, callcontext):
                    yield inferred
        except exceptions.InferenceError:
            ## XXX log error ?
            continue
nodes.Call._infer = infer_call


@bases.path_wrapper
def infer_import(self, context=None, asname=True):
    """infer an Import node: return the imported module/object"""
    name = context.lookupname
    if name is None:
        raise exceptions.InferenceError()
    if asname:
        yield self.do_import_module(self.real_name(name))
    else:
        yield self.do_import_module(name)
nodes.Import._infer = infer_import


def infer_name_module(self, name):
    context = contextmod.InferenceContext()
    context.lookupname = name
    return self.infer(context, asname=False)
nodes.Import.infer_name_module = infer_name_module


@bases.path_wrapper
def infer_import_from(self, context=None, asname=True):
    """infer a ImportFrom node: return the imported module/object"""
    name = context.lookupname
    if name is None:
        raise exceptions.InferenceError()
    if asname:
        name = self.real_name(name)
    module = self.do_import_module()
    try:
        context = contextmod.copy_context(context)
        context.lookupname = name
        stmts = module.getattr(name, ignore_locals=module is self.root())
        return bases._infer_stmts(stmts, context)
    except exceptions.NotFoundError:
        raise exceptions.InferenceError(name)
nodes.ImportFrom._infer = infer_import_from


@bases.raise_if_nothing_inferred
def infer_attribute(self, context=None):
    """infer an Attribute node by using getattr on the associated object"""
    for owner in self.expr.infer(context):
        if owner is util.YES:
            yield owner
            continue
        try:
            context.boundnode = owner
            for obj in owner.igetattr(self.attrname, context):
                yield obj
            context.boundnode = None
        except (exceptions.NotFoundError, exceptions.InferenceError):
            context.boundnode = None
        except AttributeError:
            # XXX method / function
            context.boundnode = None
nodes.Attribute._infer = bases.path_wrapper(infer_attribute)
nodes.AssignAttr.infer_lhs = infer_attribute # # won't work with a path wrapper


@bases.path_wrapper
def infer_global(self, context=None):
    if context.lookupname is None:
        raise exceptions.InferenceError()
    try:
        return bases._infer_stmts(self.root().getattr(context.lookupname),
                                  context)
    except exceptions.NotFoundError:
        raise exceptions.InferenceError()
nodes.Global._infer = infer_global


@bases.raise_if_nothing_inferred
def infer_subscript(self, context=None):
    """Inference for subscripts

    We're understanding if the index is a Const
    or a slice, passing the result of inference
    to the value's `getitem` method, which should
    handle each supported index type accordingly.
    """

    value = next(self.value.infer(context))
    if value is util.YES:
        yield util.YES
        return

    index = next(self.slice.infer(context))
    if index is util.YES:
        yield util.YES
        return

    if isinstance(index, nodes.Const):
        try:
            assigned = value.getitem(index.value, context)
        except AttributeError:
            raise exceptions.InferenceError()
        except (IndexError, TypeError):
            yield util.YES
            return

        # Prevent inferring if the infered subscript
        # is the same as the original subscripted object.
        if self is assigned or assigned is util.YES:
            yield util.YES
            return
        for infered in assigned.infer(context):
            yield infered
    else:
        raise exceptions.InferenceError()
nodes.Subscript._infer = bases.path_wrapper(infer_subscript)
nodes.Subscript.infer_lhs = infer_subscript

@bases.raise_if_nothing_inferred
def infer_unaryop(self, context=None):
    for operand in self.operand.infer(context):
        try:
            yield operand.infer_unary_op(self.op)
        except TypeError:
            continue
        except AttributeError:
            meth = protocols.UNARY_OP_METHOD[self.op]
            if meth is None:
                yield util.YES
            else:
                try:
                    # XXX just suppose if the type implement meth, returned type
                    # will be the same
                    operand.getattr(meth)
                    yield operand
                except GeneratorExit:
                    raise
                except:
                    yield util.YES
nodes.UnaryOp._infer = bases.path_wrapper(infer_unaryop)

def _infer_binop(binop, operand1, operand2, context, failures=None):
    if operand1 is util.YES:
        yield operand1
        return
    try:
        for valnode in operand1.infer_binary_op(binop, operand2, context):
            yield valnode
    except AttributeError:
        try:
            # XXX just suppose if the type implement meth, returned type
            # will be the same
            operand1.getattr(protocols.BIN_OP_METHOD[operator])
            yield operand1
        except:
            if failures is None:
                yield util.YES
            else:
                failures.append(operand1)

@bases.yes_if_nothing_inferred
def infer_binop(self, context=None):
    failures = []
    for lhs in self.left.infer(context):
        for val in _infer_binop(self, lhs, self.right, context, failures):
            yield val
    for lhs in failures:
        for rhs in self.right.infer(context):
            for val in _infer_binop(self, rhs, lhs, context):
                yield val
nodes.BinOp._infer = bases.path_wrapper(infer_binop)


def infer_arguments(self, context=None):
    name = context.lookupname
    if name is None:
        raise exceptions.InferenceError()
    return protocols._arguments_infer_argname(self, name, context)
nodes.Arguments._infer = infer_arguments


@bases.path_wrapper
def infer_assign(self, context=None):
    """infer a AssignName/AssignAttr: need to inspect the RHS part of the
    assign node
    """
    stmt = self.statement()
    if isinstance(stmt, nodes.AugAssign):
        return stmt.infer(context)

    stmts = list(self.assigned_stmts(context=context))
    return bases._infer_stmts(stmts, context)
nodes.AssignName._infer = infer_assign
nodes.AssignAttr._infer = infer_assign

def infer_augassign(self, context=None):
    failures = []
    for lhs in self.target.infer_lhs(context):
        for val in _infer_binop(self, lhs, self.value, context, failures):
            yield val
    for lhs in failures:
        for rhs in self.value.infer(context):
            for val in _infer_binop(self, rhs, lhs, context):
                yield val
nodes.AugAssign._infer = bases.path_wrapper(infer_augassign)


# no infer method on DelName and DelAttr (expected InferenceError)

@bases.path_wrapper
def infer_empty_node(self, context=None):
    if not self.has_underlying_object():
        yield util.YES
    else:
        try:
            for inferred in MANAGER.infer_ast_from_something(self.object,
                                                             context=context):
                yield inferred
        except exceptions.AstroidError:
            yield util.YES
nodes.EmptyNode._infer = infer_empty_node


def infer_index(self, context=None):
    return self.value.infer(context)
nodes.Index._infer = infer_index

# TODO: move directly into bases.Instance when the dependency hell
# will be solved.
def instance_getitem(self, index, context=None):
    # Rewrap index to Const for this case
    index = nodes.Const(index)
    if context:
        new_context = context.clone()
    else:
        context = new_context = contextmod.InferenceContext()

    # Create a new callcontext for providing index as an argument.
    new_context.callcontext = contextmod.CallContext(args=[index])
    new_context.boundnode = self

    method = next(self.igetattr('__getitem__', context=context))
    if not isinstance(method, bases.BoundMethod):
        raise exceptions.InferenceError

    try:
        return next(method.infer_call_result(self, new_context))
    except StopIteration:
        raise exceptions.InferenceError

bases.Instance.getitem = instance_getitem
