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
"""this module contains a set of functions to handle python protocols for nodes
where it makes sense.
"""

import collections
import operator
import sys

from astroid import arguments
from astroid import bases
from astroid import context as contextmod
from astroid import exceptions
from astroid import node_classes
from astroid import nodes
from astroid import util

BIN_OP_METHOD = {'+':  '__add__',
                 '-':  '__sub__',
                 '/':  '__div__',
                 '//': '__floordiv__',
                 '*':  '__mul__',
                 '**': '__pow__',
                 '%':  '__mod__',
                 '&':  '__and__',
                 '|':  '__or__',
                 '^':  '__xor__',
                 '<<': '__lshift__',
                 '>>': '__rshift__',
                 '@': '__matmul__'
                }

UNARY_OP_METHOD = {'+': '__pos__',
                   '-': '__neg__',
                   '~': '__invert__',
                   'not': None, # XXX not '__nonzero__'
                  }

# unary operations ############################################################

def tl_infer_unary_op(self, operator):
    if operator == 'not':
        return node_classes.const_factory(not bool(self.elts))
    raise TypeError() # XXX log unsupported operation
nodes.Tuple.infer_unary_op = tl_infer_unary_op
nodes.List.infer_unary_op = tl_infer_unary_op


def dict_infer_unary_op(self, operator):
    if operator == 'not':
        return node_classes.const_factory(not bool(self.items))
    raise TypeError() # XXX log unsupported operation
nodes.Dict.infer_unary_op = dict_infer_unary_op


def const_infer_unary_op(self, operator):
    if operator == 'not':
        return node_classes.const_factory(not self.value)
    # XXX log potentially raised TypeError
    elif operator == '+':
        return node_classes.const_factory(+self.value)
    else: # operator == '-':
        return node_classes.const_factory(-self.value)
nodes.Const.infer_unary_op = const_infer_unary_op


# binary operations ###########################################################

BIN_OP_IMPL = {'+':  lambda a, b: a + b,
               '-':  lambda a, b: a - b,
               '/':  lambda a, b: a / b,
               '//': lambda a, b: a // b,
               '*':  lambda a, b: a * b,
               '**': lambda a, b: a ** b,
               '%':  lambda a, b: a % b,
               '&':  lambda a, b: a & b,
               '|':  lambda a, b: a | b,
               '^':  lambda a, b: a ^ b,
               '<<': lambda a, b: a << b,
               '>>': lambda a, b: a >> b,
              }

if sys.version_info >= (3, 5):
    # MatMult is available since Python 3.5+.
    BIN_OP_IMPL['@'] = operator.matmul

for key, impl in list(BIN_OP_IMPL.items()):
    BIN_OP_IMPL[key+'='] = impl

def const_infer_binary_op(self, binop, other, context):
    operator = binop.op
    for other in other.infer(context):
        if isinstance(other, nodes.Const):
            try:
                impl = BIN_OP_IMPL[operator]

                try:
                    yield node_classes.const_factory(impl(self.value, other.value))
                except Exception:
                    # ArithmeticError is not enough: float >> float is a TypeError
                    # TODO : let pylint know about the problem
                    pass
            except TypeError:
                # XXX log TypeError
                continue
        elif other is util.YES:
            yield other
        else:
            try:
                for val in other.infer_binary_op(binop, self, context):
                    yield val
            except AttributeError:
                yield util.YES
nodes.Const.infer_binary_op = bases.yes_if_nothing_inferred(const_infer_binary_op)



def _multiply_seq_by_int(self, binop, other, context):
    node = self.__class__()
    node.parent = binop
    elts = []
    for elt in self.elts:
        infered = util.safe_infer(elt, context)
        if infered is None:
            infered = util.YES
        elts.append(infered)
    node.elts = elts * other.value
    return node


def _filter_uninferable_nodes(elts, context):
    for elt in elts:
        if elt is util.YES:
            yield elt
        else:
            for inferred in elt.infer(context):
                yield inferred


def tl_infer_binary_op(self, binop, other, context):
    operator = binop.op
    for other in other.infer(context):
        if isinstance(other, self.__class__) and operator == '+':
            node = self.__class__()
            node.parent = binop
            elts = list(_filter_uninferable_nodes(self.elts, context))
            elts += list(_filter_uninferable_nodes(other.elts, context))
            node.elts = elts
            yield node
        elif isinstance(other, nodes.Const) and operator == '*':
            if not isinstance(other.value, int):
                yield util.YES
                continue
            yield _multiply_seq_by_int(self, binop, other, context)
        elif isinstance(other, bases.Instance) and not isinstance(other, nodes.Const):
            yield util.YES
    # XXX else log TypeError
nodes.Tuple.infer_binary_op = bases.yes_if_nothing_inferred(tl_infer_binary_op)
nodes.List.infer_binary_op = bases.yes_if_nothing_inferred(tl_infer_binary_op)


def dict_infer_binary_op(self, binop, other, context):
    for other in other.infer(context):
        if isinstance(other, bases.Instance) and isinstance(other._proxied, nodes.ClassDef):
            yield util.YES
        # XXX else log TypeError
nodes.Dict.infer_binary_op = bases.yes_if_nothing_inferred(dict_infer_binary_op)

def instance_infer_binary_op(self, binop, other, context):
    operator = binop.op
    try:
        methods = self.getattr(BIN_OP_METHOD[operator])
    except (exceptions.NotFoundError, KeyError):
        # Unknown operator
        yield util.YES
    else:
        for method in methods:
            if not isinstance(method, nodes.FunctionDef):
                continue
            for result in method.infer_call_result(self, context):
                if result is not util.YES:
                    yield result
            # We are interested only in the first infered method,
            # don't go looking in the rest of the methods of the ancestors.
            break

bases.Instance.infer_binary_op = bases.yes_if_nothing_inferred(instance_infer_binary_op)


# assignment ##################################################################

"""the assigned_stmts method is responsible to return the assigned statement
(e.g. not inferred) according to the assignment type.

The `asspath` argument is used to record the lhs path of the original node.
For instance if we want assigned statements for 'c' in 'a, (b,c)', asspath
will be [1, 1] once arrived to the Assign node.

The `context` argument is the current inference context which should be given
to any intermediary inference necessary.
"""

def _resolve_looppart(parts, asspath, context):
    """recursive function to resolve multiple assignments on loops"""
    asspath = asspath[:]
    index = asspath.pop(0)
    for part in parts:
        if part is util.YES:
            continue
        # XXX handle __iter__ and log potentially detected errors
        if not hasattr(part, 'itered'):
            continue
        try:
            itered = part.itered()
        except TypeError:
            continue # XXX log error
        for stmt in itered:
            try:
                assigned = stmt.getitem(index, context)
            except (AttributeError, IndexError):
                continue
            except TypeError: # stmt is unsubscriptable Const
                continue
            if not asspath:
                # we achieved to resolved the assignment path,
                # don't infer the last part
                yield assigned
            elif assigned is util.YES:
                break
            else:
                # we are not yet on the last part of the path
                # search on each possibly inferred value
                try:
                    for inferred in _resolve_looppart(assigned.infer(context),
                                                     asspath, context):
                        yield inferred
                except exceptions.InferenceError:
                    break


@bases.raise_if_nothing_inferred
def for_assigned_stmts(self, node=None, context=None, asspath=None):
    if asspath is None:
        for lst in self.iter.infer(context):
            if isinstance(lst, (nodes.Tuple, nodes.List)):
                for item in lst.elts:
                    yield item
    else:
        for inferred in _resolve_looppart(self.iter.infer(context),
                                         asspath, context):
            yield inferred

nodes.For.assigned_stmts = for_assigned_stmts
nodes.Comprehension.assigned_stmts = for_assigned_stmts


def sequence_assigned_stmts(self, node=None, context=None, asspath=None):
    if asspath is None:
        asspath = []
    try:
        index = self.elts.index(node)
    except ValueError:
         util.reraise(exceptions.InferenceError(
             'Tried to retrieve a node {node!r} which does not exist',
             node=self, assign_path=asspath, context=context))

    asspath.insert(0, index)
    return self.parent.assigned_stmts(node=self, context=context, asspath=asspath)

nodes.Tuple.assigned_stmts = sequence_assigned_stmts
nodes.List.assigned_stmts = sequence_assigned_stmts


def assend_assigned_stmts(self, node=None, context=None, asspath=None):
    return self.parent.assigned_stmts(node=self, context=context)
nodes.AssignName.assigned_stmts = assend_assigned_stmts
nodes.AssignAttr.assigned_stmts = assend_assigned_stmts


def _arguments_infer_argname(self, name, context):
    # arguments information may be missing, in which case we can't do anything
    # more
    if not (self.args or self.vararg or self.kwarg):
        yield util.YES
        return
    # first argument of instance/class method
    if self.args and getattr(self.args[0], 'name', None) == name:
        functype = self.parent.type
        if functype == 'method':
            yield bases.Instance(self.parent.parent.frame())
            return
        if functype == 'classmethod':
            yield self.parent.parent.frame()
            return

    if context and context.callcontext:
        call_site = arguments.CallSite(context.callcontext)
        for value in call_site.infer_argument(self.parent, name, context):
            yield value
        return

    # TODO: just provide the type here, no need to have an empty Dict.
    if name == self.vararg:
        vararg = node_classes.const_factory(())
        vararg.parent = self
        yield vararg
        return
    if name == self.kwarg:
        kwarg = node_classes.const_factory({})
        kwarg.parent = self
        yield kwarg
        return
    # if there is a default value, yield it. And then yield YES to reflect
    # we can't guess given argument value
    try:
        context = contextmod.copy_context(context)
        for inferred in self.default_value(name).infer(context):
            yield inferred
        yield util.YES
    except exceptions.NoDefault:
        yield util.YES


def arguments_assigned_stmts(self, node=None, context=None, asspath=None):
    if context.callcontext:
        # reset call context/name
        callcontext = context.callcontext
        context = contextmod.copy_context(context)
        context.callcontext = None
        args = arguments.CallSite(callcontext)
        return args.infer_argument(self.parent, node.name, context)
    return _arguments_infer_argname(self, node.name, context)

nodes.Arguments.assigned_stmts = arguments_assigned_stmts


@bases.raise_if_nothing_inferred
def assign_assigned_stmts(self, node=None, context=None, asspath=None):
    if not asspath:
        yield self.value
        return
    for inferred in _resolve_asspart(self.value.infer(context), asspath, context):
        yield inferred

nodes.Assign.assigned_stmts = assign_assigned_stmts
nodes.AugAssign.assigned_stmts = assign_assigned_stmts


def _resolve_asspart(parts, asspath, context):
    """recursive function to resolve multiple assignments"""
    asspath = asspath[:]
    index = asspath.pop(0)
    for part in parts:
        if hasattr(part, 'getitem'):
            try:
                assigned = part.getitem(index, context)
            # XXX raise a specific exception to avoid potential hiding of
            # unexpected exception ?
            except (TypeError, IndexError):
                return
            if not asspath:
                # we achieved to resolved the assignment path, don't infer the
                # last part
                yield assigned
            elif assigned is util.YES:
                return
            else:
                # we are not yet on the last part of the path search on each
                # possibly inferred value
                try:
                    for inferred in _resolve_asspart(assigned.infer(context),
                                                    asspath, context):
                        yield inferred
                except exceptions.InferenceError:
                    return


@bases.raise_if_nothing_inferred
def excepthandler_assigned_stmts(self, node=None, context=None, asspath=None):
    for assigned in node_classes.unpack_infer(self.type):
        if isinstance(assigned, nodes.ClassDef):
            assigned = bases.Instance(assigned)
        yield assigned
nodes.ExceptHandler.assigned_stmts = bases.raise_if_nothing_inferred(excepthandler_assigned_stmts)


@bases.raise_if_nothing_inferred
def with_assigned_stmts(self, node=None, context=None, asspath=None):
    if asspath is None:
        for _, vars in self.items:
            if vars is None:
                continue
            for lst in vars.infer(context):
                if isinstance(lst, (nodes.Tuple, nodes.List)):
                    for item in lst.nodes:
                        yield item
nodes.With.assigned_stmts = with_assigned_stmts


@bases.yes_if_nothing_inferred
def starred_assigned_stmts(self, node=None, context=None, asspath=None):
    stmt = self.statement()
    if not isinstance(stmt, (nodes.Assign, nodes.For)):
        raise exceptions.InferenceError()

    if isinstance(stmt, nodes.Assign):
        value = stmt.value
        lhs = stmt.targets[0]

        if sum(1 for node in lhs.nodes_of_class(nodes.Starred)) > 1:
            # Too many starred arguments in the expression.
            raise exceptions.InferenceError()

        if context is None:
            context = contextmod.InferenceContext()
        try:
            rhs = next(value.infer(context))
        except exceptions.InferenceError:
            yield util.YES
            return
        if rhs is util.YES or not hasattr(rhs, 'elts'):
            # Not interested in inferred values without elts.
            yield util.YES
            return

        elts = collections.deque(rhs.elts[:])
        if len(lhs.elts) > len(rhs.elts):
            # a, *b, c = (1, 2)
            raise exceptions.InferenceError()

        # Unpack iteratively the values from the rhs of the assignment,
        # until the find the starred node. What will remain will
        # be the list of values which the Starred node will represent
        # This is done in two steps, from left to right to remove
        # anything before the starred node and from right to left
        # to remvoe anything after the starred node.

        for index, node in enumerate(lhs.elts):
            if not isinstance(node, nodes.Starred):
                elts.popleft()
                continue
            lhs_elts = collections.deque(reversed(lhs.elts[index:]))
            for node in lhs_elts:
                if not isinstance(node, nodes.Starred):
                    elts.pop()
                    continue
                # We're done
                packed = nodes.List()
                packed.elts = elts
                packed.parent = self
                yield packed
                break

nodes.Starred.assigned_stmts = starred_assigned_stmts
