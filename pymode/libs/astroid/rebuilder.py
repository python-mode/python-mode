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
"""this module contains utilities for rebuilding a _ast tree in
order to get a single Astroid representation
"""

import sys
import _ast
from _ast import (
    # binary operators
    Add, Div, FloorDiv, Mod, Mult, Pow, Sub, BitAnd, BitOr, BitXor,
    LShift, RShift,
    # logical operators
    And, Or,
    # unary operators
    UAdd, USub, Not, Invert,
    # comparison operators
    Eq, Gt, GtE, In, Is, IsNot, Lt, LtE, NotEq, NotIn,
    )

from astroid import nodes as new
from astroid import astpeephole


_BIN_OP_CLASSES = {Add: '+',
                   BitAnd: '&',
                   BitOr: '|',
                   BitXor: '^',
                   Div: '/',
                   FloorDiv: '//',
                   Mod: '%',
                   Mult: '*',
                   Pow: '**',
                   Sub: '-',
                   LShift: '<<',
                   RShift: '>>',
                  }
if sys.version_info >= (3, 5):
    from _ast import MatMult
    _BIN_OP_CLASSES[MatMult] = '@'

_BOOL_OP_CLASSES = {And: 'and',
                    Or: 'or',
                   }

_UNARY_OP_CLASSES = {UAdd: '+',
                     USub: '-',
                     Not: 'not',
                     Invert: '~',
                    }

_CMP_OP_CLASSES = {Eq: '==',
                   Gt: '>',
                   GtE: '>=',
                   In: 'in',
                   Is: 'is',
                   IsNot: 'is not',
                   Lt: '<',
                   LtE: '<=',
                   NotEq: '!=',
                   NotIn: 'not in',
                  }

CONST_NAME_TRANSFORMS = {'None':  None,
                         'True':  True,
                         'False': False,
                        }

REDIRECT = {'arguments': 'Arguments',
            'comprehension': 'Comprehension',
            "ListCompFor": 'Comprehension',
            "GenExprFor": 'Comprehension',
            'excepthandler': 'ExceptHandler',
            'keyword': 'Keyword',
           }
PY3K = sys.version_info >= (3, 0)
PY34 = sys.version_info >= (3, 4)

def _init_set_doc(node, newnode):
    newnode.doc = None
    try:
        if isinstance(node.body[0], _ast.Expr) and isinstance(node.body[0].value, _ast.Str):
            newnode.doc = node.body[0].value.s
            node.body = node.body[1:]

    except IndexError:
        pass # ast built from scratch

def _lineno_parent(oldnode, newnode, parent):
    newnode.parent = parent
    newnode.lineno = oldnode.lineno
    newnode.col_offset = oldnode.col_offset

def _set_infos(oldnode, newnode, parent):
    newnode.parent = parent
    if hasattr(oldnode, 'lineno'):
        newnode.lineno = oldnode.lineno
    if hasattr(oldnode, 'col_offset'):
        newnode.col_offset = oldnode.col_offset

def _create_yield_node(node, parent, rebuilder, factory):
    newnode = factory()
    _lineno_parent(node, newnode, parent)
    if node.value is not None:
        newnode.value = rebuilder.visit(node.value, newnode, None)
    return newnode

def _visit_or_none(node, attr, visitor, parent, assign_ctx, visit='visit',
                   **kws):
    """If the given node has an attribute, visits the attribute, and
    otherwise returns None.

    """
    value = getattr(node, attr, None)
    if value:
        return getattr(visitor, visit)(value, parent, assign_ctx, **kws)
    else:
        return None


class TreeRebuilder(object):
    """Rebuilds the _ast tree to become an Astroid tree"""

    def __init__(self, manager):
        self._manager = manager
        self.asscontext = None
        self._global_names = []
        self._import_from_nodes = []
        self._delayed_assattr = []
        self._visit_meths = {}
        self._peepholer = astpeephole.ASTPeepholeOptimizer()

    def visit_module(self, node, modname, modpath, package):
        """visit a Module node by returning a fresh instance of it"""
        newnode = new.Module(modname, None)
        newnode.package = package
        newnode.parent = None
        _init_set_doc(node, newnode)
        newnode.body = [self.visit(child, newnode) for child in node.body]
        newnode.source_file = modpath
        return newnode

    def visit(self, node, parent, assign_ctx=None):
        cls = node.__class__
        if cls in self._visit_meths:
            visit_method = self._visit_meths[cls]
        else:
            cls_name = cls.__name__
            visit_name = 'visit_' + REDIRECT.get(cls_name, cls_name).lower()
            visit_method = getattr(self, visit_name)
            self._visit_meths[cls] = visit_method
        return visit_method(node, parent, assign_ctx)

    def _save_assignment(self, node, name=None):
        """save assignement situation since node.parent is not available yet"""
        if self._global_names and node.name in self._global_names[-1]:
            node.root().set_local(node.name, node)
        else:
            node.parent.set_local(node.name, node)

    def visit_arguments(self, node, parent, assign_ctx=None):
        """visit a Arguments node by returning a fresh instance of it"""
        newnode = new.Arguments()
        newnode.parent = parent
        newnode.args = [self.visit(child, newnode, "Assign")
                        for child in node.args]
        newnode.defaults = [self.visit(child, newnode, assign_ctx)
                            for child in node.defaults]
        newnode.kwonlyargs = []
        newnode.kw_defaults = []
        vararg, kwarg = node.vararg, node.kwarg
        # change added in 82732 (7c5c678e4164), vararg and kwarg
        # are instances of `_ast.arg`, not strings
        if vararg:
            if PY34:
                if vararg.annotation:
                    newnode.varargannotation = self.visit(vararg.annotation,
                                                          newnode, assign_ctx)
                vararg = vararg.arg
            elif PY3K and node.varargannotation:
                newnode.varargannotation = self.visit(node.varargannotation,
                                                      newnode, assign_ctx)
        if kwarg:
            if PY34:
                if kwarg.annotation:
                    newnode.kwargannotation = self.visit(kwarg.annotation,
                                                         newnode, assign_ctx)
                kwarg = kwarg.arg
            elif PY3K:
                if node.kwargannotation:
                    newnode.kwargannotation = self.visit(node.kwargannotation,
                                                         newnode, assign_ctx)
        newnode.vararg = vararg
        newnode.kwarg = kwarg
        # save argument names in locals:
        if vararg:
            newnode.parent.set_local(vararg, newnode)
        if kwarg:
            newnode.parent.set_local(kwarg, newnode)
        return newnode

    def visit_assignattr(self, node, parent, assign_ctx=None):
        """visit a AssAttr node by returning a fresh instance of it"""
        newnode = new.AssignAttr()
        _lineno_parent(node, newnode, parent)
        newnode.expr = self.visit(node.expr, newnode, assign_ctx)
        self._delayed_assattr.append(newnode)
        return newnode

    def visit_assert(self, node, parent, assign_ctx=None):
        """visit a Assert node by returning a fresh instance of it"""
        newnode = new.Assert()
        _lineno_parent(node, newnode, parent)
        newnode.test = self.visit(node.test, newnode, assign_ctx)
        if node.msg is not None:
            newnode.fail = self.visit(node.msg, newnode, assign_ctx)
        return newnode

    def visit_assign(self, node, parent, assign_ctx=None):
        """visit a Assign node by returning a fresh instance of it"""
        newnode = new.Assign()
        _lineno_parent(node, newnode, parent)
        newnode.targets = [self.visit(child, newnode, "Assign")
                           for child in node.targets]
        newnode.value = self.visit(node.value, newnode, None)
        return newnode

    def visit_assignname(self, node, parent, assign_ctx=None, node_name=None):
        '''visit a node and return a AssName node'''
        newnode = new.AssignName()
        _set_infos(node, newnode, parent)
        newnode.name = node_name
        self._save_assignment(newnode)
        return newnode

    def visit_augassign(self, node, parent, assign_ctx=None):
        """visit a AugAssign node by returning a fresh instance of it"""
        newnode = new.AugAssign()
        _lineno_parent(node, newnode, parent)
        newnode.op = _BIN_OP_CLASSES[node.op.__class__] + "="
        newnode.target = self.visit(node.target, newnode, "Assign")
        newnode.value = self.visit(node.value, newnode, None)
        return newnode

    def visit_repr(self, node, parent, assign_ctx=None):
        """visit a Backquote node by returning a fresh instance of it"""
        newnode = new.Repr()
        _lineno_parent(node, newnode, parent)
        newnode.value = self.visit(node.value, newnode, assign_ctx)
        return newnode

    def visit_binop(self, node, parent, assign_ctx=None):
        """visit a BinOp node by returning a fresh instance of it"""
        if isinstance(node.left, _ast.BinOp) and self._manager.optimize_ast:
            # Optimize BinOp operations in order to remove
            # redundant recursion. For instance, if the
            # following code is parsed in order to obtain
            # its ast, then the rebuilder will fail with an
            # infinite recursion, the same will happen with the
            # inference engine as well. There's no need to hold
            # so many objects for the BinOp if they can be reduced
            # to something else (also, the optimization
            # might handle only Const binops, which isn't a big
            # problem for the correctness of the program).
            #
            # ("a" + "b" + # one thousand more + "c")
            optimized = self._peepholer.optimize_binop(node)
            if optimized:
                _lineno_parent(node, optimized, parent)
                return optimized

        newnode = new.BinOp()
        _lineno_parent(node, newnode, parent)
        newnode.left = self.visit(node.left, newnode, assign_ctx)
        newnode.right = self.visit(node.right, newnode, assign_ctx)
        newnode.op = _BIN_OP_CLASSES[node.op.__class__]
        return newnode

    def visit_boolop(self, node, parent, assign_ctx=None):
        """visit a BoolOp node by returning a fresh instance of it"""
        newnode = new.BoolOp()
        _lineno_parent(node, newnode, parent)
        newnode.values = [self.visit(child, newnode, assign_ctx)
                          for child in node.values]
        newnode.op = _BOOL_OP_CLASSES[node.op.__class__]
        return newnode

    def visit_break(self, node, parent, assign_ctx=None):
        """visit a Break node by returning a fresh instance of it"""
        newnode = new.Break()
        _set_infos(node, newnode, parent)
        return newnode

    def visit_call(self, node, parent, assign_ctx=None):
        """visit a CallFunc node by returning a fresh instance of it"""
        newnode = new.Call()
        _lineno_parent(node, newnode, parent)
        newnode.func = self.visit(node.func, newnode, assign_ctx)
        args = [self.visit(child, newnode, assign_ctx)
                for child in node.args]

        starargs = _visit_or_none(node, 'starargs', self, newnode,
                                  assign_ctx)
        kwargs = _visit_or_none(node, 'kwargs', self, newnode,
                                assign_ctx)
        keywords = None
        if node.keywords:
            keywords = [self.visit(child, newnode, assign_ctx)
                        for child in node.keywords]

        if starargs:
            new_starargs = new.Starred()
            new_starargs.col_offset = starargs.col_offset
            new_starargs.lineno = starargs.lineno
            new_starargs.parent = starargs.parent
            new_starargs.value = starargs
            args.append(new_starargs)
        if kwargs:
            new_kwargs = new.Keyword()
            new_kwargs.arg = None
            new_kwargs.col_offset = kwargs.col_offset
            new_kwargs.lineno = kwargs.lineno
            new_kwargs.parent = kwargs.parent
            new_kwargs.value = kwargs
            if keywords:
                keywords.append(new_kwargs)
            else:
                keywords = [new_kwargs]

        newnode.args = args
        newnode.keywords = keywords
        return newnode

    def visit_classdef(self, node, parent, assign_ctx=None):
        """visit a Class node to become astroid"""
        newnode = new.ClassDef(node.name, None)
        _lineno_parent(node, newnode, parent)
        _init_set_doc(node, newnode)
        newnode.bases = [self.visit(child, newnode, assign_ctx)
                         for child in node.bases]
        newnode.body = [self.visit(child, newnode, assign_ctx)
                        for child in node.body]
        if node.decorator_list:
            newnode.decorators = self.visit_decorators(node, newnode, assign_ctx)
        newnode.parent.frame().set_local(newnode.name, newnode)
        return newnode

    def visit_const(self, node, parent, assign_ctx=None):
        """visit a Const node by returning a fresh instance of it"""
        newnode = new.Const(node.value)
        _set_infos(node, newnode, parent)
        return newnode

    def visit_continue(self, node, parent, assign_ctx=None):
        """visit a Continue node by returning a fresh instance of it"""
        newnode = new.Continue()
        _set_infos(node, newnode, parent)
        return newnode

    def visit_compare(self, node, parent, assign_ctx=None):
        """visit a Compare node by returning a fresh instance of it"""
        newnode = new.Compare()
        _lineno_parent(node, newnode, parent)
        newnode.left = self.visit(node.left, newnode, assign_ctx)
        newnode.ops = [(_CMP_OP_CLASSES[op.__class__], self.visit(expr, newnode, assign_ctx))
                       for (op, expr) in zip(node.ops, node.comparators)]
        return newnode

    def visit_comprehension(self, node, parent, assign_ctx=None):
        """visit a Comprehension node by returning a fresh instance of it"""
        newnode = new.Comprehension()
        newnode.parent = parent
        newnode.target = self.visit(node.target, newnode, 'Assign')
        newnode.iter = self.visit(node.iter, newnode, None)
        newnode.ifs = [self.visit(child, newnode, None)
                       for child in node.ifs]
        return newnode

    def visit_decorators(self, node, parent, assign_ctx=None):
        """visit a Decorators node by returning a fresh instance of it"""
        # /!\ node is actually a _ast.Function node while
        # parent is a astroid.nodes.Function node
        newnode = new.Decorators()
        _lineno_parent(node, newnode, parent)
        decorators = node.decorator_list
        newnode.nodes = [self.visit(child, newnode, assign_ctx)
                         for child in decorators]
        return newnode

    def visit_delete(self, node, parent, assign_ctx=None):
        """visit a Delete node by returning a fresh instance of it"""
        newnode = new.Delete()
        _lineno_parent(node, newnode, parent)
        newnode.targets = [self.visit(child, newnode, 'Del')
                           for child in node.targets]
        return newnode

    def _visit_dict_items(self, node, parent, newnode, assign_ctx):
        for key, value in zip(node.keys, node.values):
            rebuilt_value = self.visit(value, newnode, assign_ctx)
            if not key:
                # Python 3.5 and extended unpacking
                rebuilt_key = new.DictUnpack()
                rebuilt_key.lineno = rebuilt_value.lineno
                rebuilt_key.col_offset = rebuilt_value.col_offset
                rebuilt_key.parent = rebuilt_value.parent
            else:
                rebuilt_key = self.visit(key, newnode, assign_ctx)
            yield rebuilt_key, rebuilt_value

    def visit_dict(self, node, parent, assign_ctx=None):
        """visit a Dict node by returning a fresh instance of it"""
        newnode = new.Dict()
        _lineno_parent(node, newnode, parent)
        newnode.items = list(self._visit_dict_items(node, parent, newnode, assign_ctx))
        return newnode

    def visit_dictcomp(self, node, parent, assign_ctx=None):
        """visit a DictComp node by returning a fresh instance of it"""
        newnode = new.DictComp()
        _lineno_parent(node, newnode, parent)
        newnode.key = self.visit(node.key, newnode, assign_ctx)
        newnode.value = self.visit(node.value, newnode, assign_ctx)
        newnode.generators = [self.visit(child, newnode, assign_ctx)
                              for child in node.generators]
        return newnode

    def visit_expr(self, node, parent, assign_ctx=None):
        """visit a Discard node by returning a fresh instance of it"""
        newnode = new.Expr()
        _lineno_parent(node, newnode, parent)
        newnode.value = self.visit(node.value, newnode, assign_ctx)
        return newnode

    def visit_ellipsis(self, node, parent, assign_ctx=None):
        """visit an Ellipsis node by returning a fresh instance of it"""
        newnode = new.Ellipsis()
        _set_infos(node, newnode, parent)
        return newnode

    def visit_emptynode(self, node, parent, assign_ctx=None):
        """visit an EmptyNode node by returning a fresh instance of it"""
        newnode = new.EmptyNode()
        _set_infos(node, newnode, parent)
        return newnode

    def visit_excepthandler(self, node, parent, assign_ctx=None):
        """visit an ExceptHandler node by returning a fresh instance of it"""
        newnode = new.ExceptHandler()
        _lineno_parent(node, newnode, parent)
        if node.type is not None:
            newnode.type = self.visit(node.type, newnode, assign_ctx)
        if node.name is not None:
            # /!\ node.name can be a tuple
            newnode.name = self.visit(node.name, newnode, 'Assign')
        newnode.body = [self.visit(child, newnode, None)
                        for child in node.body]
        return newnode

    def visit_exec(self, node, parent, assign_ctx=None):
        """visit an Exec node by returning a fresh instance of it"""
        newnode = new.Exec()
        _lineno_parent(node, newnode, parent)
        newnode.expr = self.visit(node.body, newnode)
        if node.globals is not None:
            newnode.globals = self.visit(node.globals, newnode,
                                         assign_ctx)
        if node.locals is not None:
            newnode.locals = self.visit(node.locals, newnode,
                                        assign_ctx)
        return newnode

    def visit_extslice(self, node, parent, assign_ctx=None):
        """visit an ExtSlice node by returning a fresh instance of it"""
        newnode = new.ExtSlice()
        newnode.parent = parent
        newnode.dims = [self.visit(dim, newnode, assign_ctx)
                        for dim in node.dims]
        return newnode

    def _visit_for(self, cls, node, parent, assign_ctx=None):
        """visit a For node by returning a fresh instance of it"""
        newnode = cls()
        _lineno_parent(node, newnode, parent)
        newnode.target = self.visit(node.target, newnode, "Assign")
        newnode.iter = self.visit(node.iter, newnode, None)
        newnode.body = [self.visit(child, newnode, None)
                        for child in node.body]
        newnode.orelse = [self.visit(child, newnode, None)
                          for child in node.orelse]
        return newnode

    def visit_for(self, node, parent, assign_ctx=None):
        return self._visit_for(new.For, node, parent,
                               assign_ctx=assign_ctx)
    def visit_importfrom(self, node, parent, assign_ctx=None):
        """visit a From node by returning a fresh instance of it"""
        names = [(alias.name, alias.asname) for alias in node.names]
        newnode = new.ImportFrom(node.module or '', names, node.level or None)
        _set_infos(node, newnode, parent)
        # store From names to add them to locals after building
        self._import_from_nodes.append(newnode)
        return newnode

    def _visit_functiondef(self, cls, node, parent, assign_ctx=None):
        """visit an FunctionDef node to become astroid"""
        self._global_names.append({})
        newnode = cls(node.name, None)
        _lineno_parent(node, newnode, parent)
        _init_set_doc(node, newnode)
        newnode.args = self.visit(node.args, newnode, assign_ctx)
        newnode.body = [self.visit(child, newnode, assign_ctx)
                        for child in node.body]
        decorators = node.decorator_list
        if decorators:
            newnode.decorators = self.visit_decorators(
                    node, newnode, assign_ctx)
        if PY3K and node.returns:
            newnode.returns = self.visit(node.returns, newnode,
                                         assign_ctx)
        self._global_names.pop()
        frame = newnode.parent.frame()
        frame.set_local(newnode.name, newnode)
        return newnode

    def visit_functiondef(self, node, parent, assign_ctx=None):
        return self._visit_functiondef(new.FunctionDef, node, parent,
                                       assign_ctx=assign_ctx)

    def visit_generatorexp(self, node, parent, assign_ctx=None):
        """visit a GenExpr node by returning a fresh instance of it"""
        newnode = new.GeneratorExp()
        _lineno_parent(node, newnode, parent)
        newnode.elt = self.visit(node.elt, newnode, assign_ctx)
        newnode.generators = [self.visit(child, newnode, assign_ctx)
                              for child in node.generators]
        return newnode

    def visit_attribute(self, node, parent, assign_ctx=None):
        """visit a Getattr node by returning a fresh instance of it"""
        # pylint: disable=redefined-variable-type
        if assign_ctx == "Del":
            # FIXME : maybe we should reintroduce and visit_delattr ?
            # for instance, deactivating asscontext
            newnode = new.DelAttr()
        elif assign_ctx == "Assign":
            # FIXME : maybe we should call visit_assattr ?
            # Prohibit a local save if we are in an ExceptHandler.
            newnode = new.AssignAttr()
            if not isinstance(parent, new.ExceptHandler):
                self._delayed_assattr.append(newnode)
        else:
            newnode = new.Attribute()
        _lineno_parent(node, newnode, parent)
        newnode.expr = self.visit(node.value, newnode, None)
        newnode.attrname = node.attr
        return newnode

    def visit_global(self, node, parent, assign_ctx=None):
        """visit an Global node to become astroid"""
        newnode = new.Global(node.names)
        _set_infos(node, newnode, parent)
        if self._global_names: # global at the module level, no effect
            for name in node.names:
                self._global_names[-1].setdefault(name, []).append(newnode)
        return newnode

    def visit_if(self, node, parent, assign_ctx=None):
        """visit a If node by returning a fresh instance of it"""
        newnode = new.If()
        _lineno_parent(node, newnode, parent)
        newnode.test = self.visit(node.test, newnode, assign_ctx)
        newnode.body = [self.visit(child, newnode, assign_ctx)
                        for child in node.body]
        newnode.orelse = [self.visit(child, newnode, assign_ctx)
                          for child in node.orelse]
        return newnode

    def visit_ifexp(self, node, parent, assign_ctx=None):
        """visit a IfExp node by returning a fresh instance of it"""
        newnode = new.IfExp()
        _lineno_parent(node, newnode, parent)
        newnode.test = self.visit(node.test, newnode, assign_ctx)
        newnode.body = self.visit(node.body, newnode, assign_ctx)
        newnode.orelse = self.visit(node.orelse, newnode, assign_ctx)
        return newnode

    def visit_import(self, node, parent, assign_ctx=None):
        """visit a Import node by returning a fresh instance of it"""
        newnode = new.Import()
        _set_infos(node, newnode, parent)
        newnode.names = [(alias.name, alias.asname) for alias in node.names]
        # save import names in parent's locals:
        for (name, asname) in newnode.names:
            name = asname or name
            newnode.parent.set_local(name.split('.')[0], newnode)
        return newnode

    def visit_index(self, node, parent, assign_ctx=None):
        """visit a Index node by returning a fresh instance of it"""
        newnode = new.Index()
        newnode.parent = parent
        newnode.value = self.visit(node.value, newnode, assign_ctx)
        return newnode

    def visit_keyword(self, node, parent, assign_ctx=None):
        """visit a Keyword node by returning a fresh instance of it"""
        newnode = new.Keyword()
        newnode.parent = parent
        newnode.arg = node.arg
        newnode.value = self.visit(node.value, newnode, assign_ctx)
        return newnode

    def visit_lambda(self, node, parent, assign_ctx=None):
        """visit a Lambda node by returning a fresh instance of it"""
        newnode = new.Lambda()
        _lineno_parent(node, newnode, parent)
        newnode.args = self.visit(node.args, newnode, assign_ctx)
        newnode.body = self.visit(node.body, newnode, assign_ctx)
        return newnode

    def visit_list(self, node, parent, assign_ctx=None):
        """visit a List node by returning a fresh instance of it"""
        newnode = new.List()
        _lineno_parent(node, newnode, parent)
        newnode.elts = [self.visit(child, newnode, assign_ctx)
                        for child in node.elts]
        return newnode

    def visit_listcomp(self, node, parent, assign_ctx=None):
        """visit a ListComp node by returning a fresh instance of it"""
        newnode = new.ListComp()
        _lineno_parent(node, newnode, parent)
        newnode.elt = self.visit(node.elt, newnode, assign_ctx)
        newnode.generators = [self.visit(child, newnode, assign_ctx)
                              for child in node.generators]
        return newnode

    def visit_name(self, node, parent, assign_ctx=None):
        """visit a Name node by returning a fresh instance of it"""
        # True and False can be assigned to something in py2x, so we have to
        # check first the asscontext
        # pylint: disable=redefined-variable-type
        if assign_ctx == "Del":
            newnode = new.DelName()
        elif assign_ctx is not None: # Ass
            newnode = new.AssName()
        elif node.id in CONST_NAME_TRANSFORMS:
            newnode = new.Const(CONST_NAME_TRANSFORMS[node.id])
            _set_infos(node, newnode, parent)
            return newnode
        else:
            newnode = new.Name()
        _lineno_parent(node, newnode, parent)
        newnode.name = node.id
        # XXX REMOVE me :
        if assign_ctx in ('Del', 'Assign'): # 'Aug' ??
            self._save_assignment(newnode)
        return newnode

    def visit_bytes(self, node, parent, assign_ctx=None):
        """visit a Bytes node by returning a fresh instance of Const"""
        newnode = new.Const(node.s)
        _set_infos(node, newnode, parent)
        return newnode

    def visit_num(self, node, parent, assign_ctx=None):
        """visit a Num node by returning a fresh instance of Const"""
        newnode = new.Const(node.n)
        _set_infos(node, newnode, parent)
        return newnode

    def visit_pass(self, node, parent, assign_ctx=None):
        """visit a Pass node by returning a fresh instance of it"""
        newnode = new.Pass()
        _set_infos(node, newnode, parent)
        return newnode

    def visit_str(self, node, parent, assign_ctx=None):
        """visit a Str node by returning a fresh instance of Const"""
        newnode = new.Const(node.s)
        _set_infos(node, newnode, parent)
        return newnode

    def visit_print(self, node, parent, assign_ctx=None):
        """visit a Print node by returning a fresh instance of it"""
        newnode = new.Print()
        _lineno_parent(node, newnode, parent)
        newnode.nl = node.nl
        if node.dest is not None:
            newnode.dest = self.visit(node.dest, newnode, assign_ctx)
        newnode.values = [self.visit(child, newnode, assign_ctx)
                          for child in node.values]
        return newnode

    def visit_raise(self, node, parent, assign_ctx=None):
        """visit a Raise node by returning a fresh instance of it"""
        newnode = new.Raise()
        _lineno_parent(node, newnode, parent)
        if node.type is not None:
            newnode.exc = self.visit(node.type, newnode, assign_ctx)
        if node.inst is not None:
            newnode.inst = self.visit(node.inst, newnode, assign_ctx)
        if node.tback is not None:
            newnode.tback = self.visit(node.tback, newnode, assign_ctx)
        return newnode

    def visit_return(self, node, parent, assign_ctx=None):
        """visit a Return node by returning a fresh instance of it"""
        newnode = new.Return()
        _lineno_parent(node, newnode, parent)
        if node.value is not None:
            newnode.value = self.visit(node.value, newnode, assign_ctx)
        return newnode

    def visit_set(self, node, parent, assign_ctx=None):
        """visit a Set node by returning a fresh instance of it"""
        newnode = new.Set()
        _lineno_parent(node, newnode, parent)
        newnode.elts = [self.visit(child, newnode, assign_ctx)
                        for child in node.elts]
        return newnode

    def visit_setcomp(self, node, parent, assign_ctx=None):
        """visit a SetComp node by returning a fresh instance of it"""
        newnode = new.SetComp()
        _lineno_parent(node, newnode, parent)
        newnode.elt = self.visit(node.elt, newnode, assign_ctx)
        newnode.generators = [self.visit(child, newnode, assign_ctx)
                              for child in node.generators]
        return newnode

    def visit_slice(self, node, parent, assign_ctx=None):
        """visit a Slice node by returning a fresh instance of it"""
        newnode = new.Slice()
        newnode.parent = parent
        if node.lower is not None:
            newnode.lower = self.visit(node.lower, newnode, assign_ctx)
        if node.upper is not None:
            newnode.upper = self.visit(node.upper, newnode, assign_ctx)
        if node.step is not None:
            newnode.step = self.visit(node.step, newnode, assign_ctx)
        return newnode

    def visit_subscript(self, node, parent, assign_ctx=None):
        """visit a Subscript node by returning a fresh instance of it"""
        newnode = new.Subscript()
        _lineno_parent(node, newnode, parent)
        newnode.value = self.visit(node.value, newnode, None)
        newnode.slice = self.visit(node.slice, newnode, None)
        return newnode

    def visit_tryexcept(self, node, parent, assign_ctx=None):
        """visit a TryExcept node by returning a fresh instance of it"""
        newnode = new.TryExcept()
        _lineno_parent(node, newnode, parent)
        newnode.body = [self.visit(child, newnode, assign_ctx)
                        for child in node.body]
        newnode.handlers = [self.visit(child, newnode, assign_ctx)
                            for child in node.handlers]
        newnode.orelse = [self.visit(child, newnode, assign_ctx)
                          for child in node.orelse]
        return newnode

    def visit_tryfinally(self, node, parent, assign_ctx=None):
        """visit a TryFinally node by returning a fresh instance of it"""
        newnode = new.TryFinally()
        _lineno_parent(node, newnode, parent)
        newnode.body = [self.visit(child, newnode, assign_ctx)
                        for child in node.body]
        newnode.finalbody = [self.visit(n, newnode, assign_ctx)
                             for n in node.finalbody]
        return newnode

    def visit_tuple(self, node, parent, assign_ctx=None):
        """visit a Tuple node by returning a fresh instance of it"""
        newnode = new.Tuple()
        _lineno_parent(node, newnode, parent)
        newnode.elts = [self.visit(child, newnode, assign_ctx)
                        for child in node.elts]
        return newnode

    def visit_unaryop(self, node, parent, assign_ctx=None):
        """visit a UnaryOp node by returning a fresh instance of it"""
        newnode = new.UnaryOp()
        _lineno_parent(node, newnode, parent)
        newnode.operand = self.visit(node.operand, newnode, assign_ctx)
        newnode.op = _UNARY_OP_CLASSES[node.op.__class__]
        return newnode

    def visit_while(self, node, parent, assign_ctx=None):
        """visit a While node by returning a fresh instance of it"""
        newnode = new.While()
        _lineno_parent(node, newnode, parent)
        newnode.test = self.visit(node.test, newnode, assign_ctx)
        newnode.body = [self.visit(child, newnode, assign_ctx)
                        for child in node.body]
        newnode.orelse = [self.visit(child, newnode, assign_ctx)
                          for child in node.orelse]
        return newnode

    def visit_with(self, node, parent, assign_ctx=None):
        newnode = new.With()
        _lineno_parent(node, newnode, parent)
        expr = self.visit(node.context_expr, newnode, assign_ctx)
        if node.optional_vars is not None:
            vars = self.visit(node.optional_vars, newnode, 'Assign')
        else:
            vars = None
        self.asscontext = None
        newnode.items = [(expr, vars)]
        newnode.body = [self.visit(child, newnode, assign_ctx)
                        for child in node.body]
        return newnode

    def visit_yield(self, node, parent, assign_ctx=None):
        """visit a Yield node by returning a fresh instance of it"""
        return _create_yield_node(node, parent, self, new.Yield)

class TreeRebuilder3k(TreeRebuilder):
    """extend and overwrite TreeRebuilder for python3k"""

    def visit_arg(self, node, parent, assign_ctx=None):
        """visit a arg node by returning a fresh AssName instance"""
        # TODO(cpopa): introduce an Arg node instead of using AssignName.
        return self.visit_assignname(node, parent, assign_ctx, node.arg)

    def visit_nameconstant(self, node, parent, assign_ctx=None):
        # in Python 3.4 we have NameConstant for True / False / None
        newnode = new.Const(node.value)
        _set_infos(node, newnode, parent)
        return newnode

    def visit_arguments(self, node, parent, assign_ctx=None):
        newnode = super(TreeRebuilder3k, self).visit_arguments(node, parent, assign_ctx)
        newnode.kwonlyargs = [self.visit(child, newnode, 'Assign')
                              for child in node.kwonlyargs]
        newnode.kw_defaults = [self.visit(child, newnode, None)
                               if child else None for child in node.kw_defaults]
        newnode.annotations = [
            self.visit(arg.annotation, newnode, None) if arg.annotation else None
            for arg in node.args]
        return newnode

    def visit_excepthandler(self, node, parent, assign_ctx=None):
        """visit an ExceptHandler node by returning a fresh instance of it"""
        newnode = new.ExceptHandler()
        _lineno_parent(node, newnode, parent)
        if node.type is not None:
            newnode.type = self.visit(node.type, newnode, assign_ctx)
        if node.name is not None:
            newnode.name = self.visit_assignname(node, newnode, 'Assign', node.name)
        newnode.body = [self.visit(child, newnode, None)
                        for child in node.body]
        return newnode

    def visit_nonlocal(self, node, parent, assign_ctx=None):
        """visit a Nonlocal node and return a new instance of it"""
        newnode = new.Nonlocal(node.names)
        _set_infos(node, newnode, parent)
        return newnode

    def visit_raise(self, node, parent, assign_ctx=None):
        """visit a Raise node by returning a fresh instance of it"""
        newnode = new.Raise()
        _lineno_parent(node, newnode, parent)
        # no traceback; anyway it is not used in Pylint
        if node.exc is not None:
            newnode.exc = self.visit(node.exc, newnode, assign_ctx)
        if node.cause is not None:
            newnode.cause = self.visit(node.cause, newnode, assign_ctx)
        return newnode

    def visit_starred(self, node, parent, assign_ctx=None):
        """visit a Starred node and return a new instance of it"""
        newnode = new.Starred()
        _lineno_parent(node, newnode, parent)
        newnode.value = self.visit(node.value, newnode, assign_ctx)
        return newnode

    def visit_try(self, node, parent, assign_ctx=None):
        # python 3.3 introduce a new Try node replacing TryFinally/TryExcept nodes
        # pylint: disable=redefined-variable-type
        if node.finalbody:
            newnode = new.TryFinally()
            _lineno_parent(node, newnode, parent)
            newnode.finalbody = [self.visit(n, newnode, assign_ctx)
                                 for n in node.finalbody]
            if node.handlers:
                excnode = new.TryExcept()
                _lineno_parent(node, excnode, newnode)
                excnode.body = [self.visit(child, excnode, assign_ctx)
                                for child in node.body]
                excnode.handlers = [self.visit(child, excnode, assign_ctx)
                                    for child in node.handlers]
                excnode.orelse = [self.visit(child, excnode, assign_ctx)
                                  for child in node.orelse]
                newnode.body = [excnode]
            else:
                newnode.body = [self.visit(child, newnode, assign_ctx)
                                for child in node.body]
        elif node.handlers:
            newnode = new.TryExcept()
            _lineno_parent(node, newnode, parent)
            newnode.body = [self.visit(child, newnode, assign_ctx)
                            for child in node.body]
            newnode.handlers = [self.visit(child, newnode, assign_ctx)
                                for child in node.handlers]
            newnode.orelse = [self.visit(child, newnode, assign_ctx)
                              for child in node.orelse]
        return newnode

    def _visit_with(self, cls, node, parent, assign_ctx=None):
        if 'items' not in node._fields:
            # python < 3.3
            return super(TreeRebuilder3k, self).visit_with(node, parent,
                                                           assign_ctx)

        newnode = cls()
        _lineno_parent(node, newnode, parent)
        def visit_child(child):
            expr = self.visit(child.context_expr, newnode)
            if child.optional_vars:
                var = self.visit(child.optional_vars, newnode,
                                 'Assign')
            else:
                var = None
            return expr, var
        newnode.items = [visit_child(child)
                         for child in node.items]
        newnode.body = [self.visit(child, newnode, None)
                        for child in node.body]
        return newnode

    def visit_with(self, node, parent, assign_ctx=None):
        return self._visit_with(new.With, node, parent, assign_ctx=assign_ctx)

    def visit_yieldfrom(self, node, parent, assign_ctx=None):
        return _create_yield_node(node, parent, self, new.YieldFrom)

    def visit_classdef(self, node, parent, assign_ctx=None):
        newnode = super(TreeRebuilder3k, self).visit_classdef(node, parent, assign_ctx)
        newnode._newstyle = True
        for keyword in node.keywords:
            if keyword.arg == 'metaclass':
                newnode._metaclass = self.visit(keyword, newnode, assign_ctx).value
                break
        return newnode

    # Async structs added in Python 3.5
    def visit_asyncfunctiondef(self, node, parent, assign_ctx=None):
        return self._visit_functiondef(new.AsyncFunctionDef, node, parent,
                                       assign_ctx=assign_ctx)


    def visit_asyncfor(self, node, parent, assign_ctx=None):
        return self._visit_for(new.AsyncFor, node, parent,
                               assign_ctx=assign_ctx)

    def visit_await(self, node, parent, assign_ctx=None):
        newnode = new.Await()
        newnode.lineno = node.lineno
        newnode.col_offset = node.col_offset
        newnode.parent = parent
        newnode.value = self.visit(node.value, newnode, None)
        return newnode

    def visit_asyncwith(self, node, parent, assign_ctx=None):
        return self._visit_with(new.AsyncWith, node, parent,
                                assign_ctx=assign_ctx)


if sys.version_info >= (3, 0):
    TreeRebuilder = TreeRebuilder3k
