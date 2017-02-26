# copyright 2003-2015 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
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

"""
Inference objects are a way to represent composite AST nodes,
which are used only as inference results, so they can't be found in the
code tree. For instance, inferring the following frozenset use, leads to an
inferred FrozenSet:

    CallFunc(func=Name('frozenset'), args=Tuple(...))

"""

import six

from astroid import MANAGER
from astroid.bases import (
    BUILTINS, NodeNG, Instance, _infer_stmts,
    BoundMethod, _is_property
)
from astroid.decorators import cachedproperty
from astroid.exceptions import (
    SuperError, SuperArgumentTypeError,
    NotFoundError, MroError
)
from astroid.node_classes import const_factory
from astroid.scoped_nodes import ClassDef, FunctionDef
from astroid.mixins import ParentAssignTypeMixin


class FrozenSet(NodeNG, Instance, ParentAssignTypeMixin):
    """class representing a FrozenSet composite node"""

    def __init__(self, elts=None):
        if elts is None:
            self.elts = []
        else:
            self.elts = [const_factory(e) for e in elts]

    def pytype(self):
        return '%s.frozenset' % BUILTINS

    def itered(self):
        return self.elts

    def _infer(self, context=None):
        yield self

    @cachedproperty
    def _proxied(self):
        builtins = MANAGER.astroid_cache[BUILTINS]
        return builtins.getattr('frozenset')[0]


class Super(NodeNG):
    """Proxy class over a super call.

    This class offers almost the same behaviour as Python's super,
    which is MRO lookups for retrieving attributes from the parents.

    The *mro_pointer* is the place in the MRO from where we should
    start looking, not counting it. *mro_type* is the object which
    provides the MRO, it can be both a type or an instance.
    *self_class* is the class where the super call is, while
    *scope* is the function where the super call is.
    """

    def __init__(self, mro_pointer, mro_type, self_class, scope):
        self.type = mro_type
        self.mro_pointer = mro_pointer
        self._class_based = False
        self._self_class = self_class
        self._scope = scope
        self._model = {
            '__thisclass__': self.mro_pointer,
            '__self_class__': self._self_class,
            '__self__': self.type,
            '__class__': self._proxied,
        }

    def _infer(self, context=None):
        yield self

    def super_mro(self):
        """Get the MRO which will be used to lookup attributes in this super."""
        if not isinstance(self.mro_pointer, ClassDef):
            raise SuperArgumentTypeError("The first super argument must be type.")

        if isinstance(self.type, ClassDef):
            # `super(type, type)`, most likely in a class method.
            self._class_based = True
            mro_type = self.type
        else:
            mro_type = getattr(self.type, '_proxied', None)
            if not isinstance(mro_type, (Instance, ClassDef)):
                raise SuperArgumentTypeError("super(type, obj): obj must be an "
                                             "instance or subtype of type")

        if not mro_type.newstyle:
            raise SuperError("Unable to call super on old-style classes.")

        mro = mro_type.mro()
        if self.mro_pointer not in mro:
            raise SuperArgumentTypeError("super(type, obj): obj must be an "
                                         "instance or subtype of type")

        index = mro.index(self.mro_pointer)
        return mro[index + 1:]

    @cachedproperty
    def _proxied(self):
        builtins = MANAGER.astroid_cache[BUILTINS]
        return builtins.getattr('super')[0]

    def pytype(self):
        return '%s.super' % BUILTINS

    def display_type(self):
        return 'Super of'

    @property
    def name(self):
        """Get the name of the MRO pointer."""
        return self.mro_pointer.name

    def igetattr(self, name, context=None):
        """Retrieve the inferred values of the given attribute name."""

        local_name = self._model.get(name)
        if local_name:
            yield local_name
            return

        try:
            mro = self.super_mro()
        except (MroError, SuperError) as exc:
            # Don't let invalid MROs or invalid super calls
            # to leak out as is from this function.
            six.raise_from(NotFoundError, exc)

        found = False
        for cls in mro:
            if name not in cls._locals:
                continue

            found = True
            for infered in _infer_stmts([cls[name]], context, frame=self):
                if not isinstance(infered, FunctionDef):
                    yield infered
                    continue

                # We can obtain different descriptors from a super depending
                # on what we are accessing and where the super call is.
                if infered.type == 'classmethod':
                    yield BoundMethod(infered, cls)
                elif self._scope.type == 'classmethod' and infered.type == 'method':
                    yield infered
                elif self._class_based or infered.type == 'staticmethod':
                    yield infered
                elif _is_property(infered):
                    # TODO: support other descriptors as well.
                    for value in infered.infer_call_result(self, context):
                        yield value
                else:
                    yield BoundMethod(infered, cls)

        if not found:
            raise NotFoundError(name)

    def getattr(self, name, context=None):
        return list(self.igetattr(name, context=context))
