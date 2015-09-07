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

__doctype__ = "restructuredtext en"

from itertools import chain

from astroid import nodes

from astroid.manager import AstroidManager
from astroid.exceptions import (AstroidError, InferenceError, NoDefault,
                                NotFoundError, UnresolvableName)
from astroid.bases import (YES, Instance, InferenceContext,
                           _infer_stmts, copy_context, path_wrapper,
                           raise_if_nothing_infered)
from astroid.protocols import (
    _arguments_infer_argname,
    BIN_OP_METHOD, UNARY_OP_METHOD)

MANAGER = AstroidManager()


class CallContext(object):
    """when inferring a function call, this class is used to remember values
    given as argument
    """
    def __init__(self, args, starargs, dstarargs):
        self.args = []
        self.nargs = {}
        for arg in args:
            if isinstance(arg, nodes.Keyword):
                self.nargs[arg.arg] = arg.value
            else:
                self.args.append(arg)
        self.starargs = starargs
        self.dstarargs = dstarargs

    def infer_argument(self, funcnode, name, context):
        """infer a function argument value according to the call context"""
        # 1. search in named keywords
        try:
            return self.nargs[name].infer(context)
        except KeyError:
            # Function.args.args can be None in astroid (means that we don't have
            # information on argnames)
            argindex = funcnode.args.find_argname(name)[0]
            if argindex is not None:
                # 2. first argument of instance/class method
                if argindex == 0 and funcnode.type in ('method', 'classmethod'):
                    if context.boundnode is not None:
                        boundnode = context.boundnode
                    else:
                        # XXX can do better ?
                        boundnode = funcnode.parent.frame()
                    if funcnode.type == 'method':
                        if not isinstance(boundnode, Instance):
                            boundnode = Instance(boundnode)
                        return iter((boundnode,))
                    if funcnode.type == 'classmethod':
                        return iter((boundnode,))
                # if we have a method, extract one position
                # from the index, so we'll take in account
                # the extra parameter represented by `self` or `cls`
                if funcnode.type in ('method', 'classmethod'):
                    argindex -= 1
                # 2. search arg index
                try:
                    return self.args[argindex].infer(context)
                except IndexError:
                    pass
                # 3. search in *args (.starargs)
                if self.starargs is not None:
                    its = []
                    for infered in self.starargs.infer(context):
                        if infered is YES:
                            its.append((YES,))
                            continue
                        try:
                            its.append(infered.getitem(argindex, context).infer(context))
                        except (InferenceError, AttributeError):
                            its.append((YES,))
                        except (IndexError, TypeError):
                            continue
                    if its:
                        return chain(*its)
        # 4. XXX search in **kwargs (.dstarargs)
        if self.dstarargs is not None:
            its = []
            for infered in self.dstarargs.infer(context):
                if infered is YES:
                    its.append((YES,))
                    continue
                try:
                    its.append(infered.getitem(name, context).infer(context))
                except (InferenceError, AttributeError):
                    its.append((YES,))
                except (IndexError, TypeError):
                    continue
            if its:
                return chain(*its)
        # 5. */** argument, (Tuple or Dict)
        if name == funcnode.args.vararg:
            return iter((nodes.const_factory(())))
        if name == funcnode.args.kwarg:
            return iter((nodes.const_factory({})))
        # 6. return default value if any
        try:
            return funcnode.args.default_value(name).infer(context)
        except NoDefault:
            raise InferenceError(name)


# .infer method ###############################################################


def infer_end(self, context=None):
    """inference's end for node such as Module, Class, Function, Const...
    """
    yield self
nodes.Module._infer = infer_end
nodes.Class._infer = infer_end
nodes.Function._infer = infer_end
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
    while current.parent and not isinstance(current.parent, nodes.Function):
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
            raise UnresolvableName(self.name)
    context = context.clone()
    context.lookupname = self.name
    return _infer_stmts(stmts, context, frame)
nodes.Name._infer = path_wrapper(infer_name)
nodes.AssName.infer_lhs = infer_name # won't work with a path wrapper


def infer_callfunc(self, context=None):
    """infer a CallFunc node by trying to guess what the function returns"""
    callcontext = context.clone()
    callcontext.callcontext = CallContext(self.args, self.starargs, self.kwargs)
    callcontext.boundnode = None
    for callee in self.func.infer(context):
        if callee is YES:
            yield callee
            continue
        try:
            if hasattr(callee, 'infer_call_result'):
                for infered in callee.infer_call_result(self, callcontext):
                    yield infered
        except InferenceError:
            ## XXX log error ?
            continue
nodes.CallFunc._infer = path_wrapper(raise_if_nothing_infered(infer_callfunc))


def infer_import(self, context=None, asname=True):
    """infer an Import node: return the imported module/object"""
    name = context.lookupname
    if name is None:
        raise InferenceError()
    if asname:
        yield self.do_import_module(self.real_name(name))
    else:
        yield self.do_import_module(name)
nodes.Import._infer = path_wrapper(infer_import)

def infer_name_module(self, name):
    context = InferenceContext()
    context.lookupname = name
    return self.infer(context, asname=False)
nodes.Import.infer_name_module = infer_name_module


def infer_from(self, context=None, asname=True):
    """infer a From nodes: return the imported module/object"""
    name = context.lookupname
    if name is None:
        raise InferenceError()
    if asname:
        name = self.real_name(name)
    module = self.do_import_module()
    try:
        context = copy_context(context)
        context.lookupname = name
        return _infer_stmts(module.getattr(name, ignore_locals=module is self.root()), context)
    except NotFoundError:
        raise InferenceError(name)
nodes.From._infer = path_wrapper(infer_from)


def infer_getattr(self, context=None):
    """infer a Getattr node by using getattr on the associated object"""
    for owner in self.expr.infer(context):
        if owner is YES:
            yield owner
            continue
        try:
            context.boundnode = owner
            for obj in owner.igetattr(self.attrname, context):
                yield obj
            context.boundnode = None
        except (NotFoundError, InferenceError):
            context.boundnode = None
        except AttributeError:
            # XXX method / function
            context.boundnode = None
nodes.Getattr._infer = path_wrapper(raise_if_nothing_infered(infer_getattr))
nodes.AssAttr.infer_lhs = raise_if_nothing_infered(infer_getattr) # # won't work with a path wrapper


def infer_global(self, context=None):
    if context.lookupname is None:
        raise InferenceError()
    try:
        return _infer_stmts(self.root().getattr(context.lookupname), context)
    except NotFoundError:
        raise InferenceError()
nodes.Global._infer = path_wrapper(infer_global)


def infer_subscript(self, context=None):
    """infer simple subscription such as [1,2,3][0] or (1,2,3)[-1]"""
    value = next(self.value.infer(context))
    if value is YES:
        yield YES
        return

    index = next(self.slice.infer(context))
    if index is YES:
        yield YES
        return

    if isinstance(index, nodes.Const):
        try:
            assigned = value.getitem(index.value, context)
        except AttributeError:
            raise InferenceError()
        except (IndexError, TypeError):
            yield YES
            return

        # Prevent inferring if the infered subscript
        # is the same as the original subscripted object.
        if self is assigned:
            yield YES
            return
        for infered in assigned.infer(context):
            yield infered
    else:
        raise InferenceError()
nodes.Subscript._infer = path_wrapper(infer_subscript)
nodes.Subscript.infer_lhs = raise_if_nothing_infered(infer_subscript)

def infer_unaryop(self, context=None):
    for operand in self.operand.infer(context):
        try:
            yield operand.infer_unary_op(self.op)
        except TypeError:
            continue
        except AttributeError:
            meth = UNARY_OP_METHOD[self.op]
            if meth is None:
                yield YES
            else:
                try:
                    # XXX just suppose if the type implement meth, returned type
                    # will be the same
                    operand.getattr(meth)
                    yield operand
                except GeneratorExit:
                    raise
                except:
                    yield YES
nodes.UnaryOp._infer = path_wrapper(infer_unaryop)

def _infer_binop(operator, operand1, operand2, context, failures=None):
    if operand1 is YES:
        yield operand1
        return
    try:
        for valnode in operand1.infer_binary_op(operator, operand2, context):
            yield valnode
    except AttributeError:
        try:
            # XXX just suppose if the type implement meth, returned type
            # will be the same
            operand1.getattr(BIN_OP_METHOD[operator])
            yield operand1
        except:
            if failures is None:
                yield YES
            else:
                failures.append(operand1)

def infer_binop(self, context=None):
    failures = []
    for lhs in self.left.infer(context):
        for val in _infer_binop(self.op, lhs, self.right, context, failures):
            yield val
    for lhs in failures:
        for rhs in self.right.infer(context):
            for val in _infer_binop(self.op, rhs, lhs, context):
                yield val
nodes.BinOp._infer = path_wrapper(infer_binop)


def infer_arguments(self, context=None):
    name = context.lookupname
    if name is None:
        raise InferenceError()
    return _arguments_infer_argname(self, name, context)
nodes.Arguments._infer = infer_arguments


def infer_ass(self, context=None):
    """infer a AssName/AssAttr: need to inspect the RHS part of the
    assign node
    """
    stmt = self.statement()
    if isinstance(stmt, nodes.AugAssign):
        return stmt.infer(context)
    stmts = list(self.assigned_stmts(context=context))
    return _infer_stmts(stmts, context)
nodes.AssName._infer = path_wrapper(infer_ass)
nodes.AssAttr._infer = path_wrapper(infer_ass)

def infer_augassign(self, context=None):
    failures = []
    for lhs in self.target.infer_lhs(context):
        for val in _infer_binop(self.op, lhs, self.value, context, failures):
            yield val
    for lhs in failures:
        for rhs in self.value.infer(context):
            for val in _infer_binop(self.op, rhs, lhs, context):
                yield val
nodes.AugAssign._infer = path_wrapper(infer_augassign)


# no infer method on DelName and DelAttr (expected InferenceError)


def infer_empty_node(self, context=None):
    if not self.has_underlying_object():
        yield YES
    else:
        try:
            for infered in MANAGER.infer_ast_from_something(self.object,
                                                            context=context):
                yield infered
        except AstroidError:
            yield YES
nodes.EmptyNode._infer = path_wrapper(infer_empty_node)


def infer_index(self, context=None):
    return self.value.infer(context)
nodes.Index._infer = infer_index
