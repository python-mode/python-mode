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
#
# The code in this file was originally part of logilab-common, licensed under
# the same license.
import warnings

from astroid import exceptions


def generate_warning(message, warning):
    return lambda *args: warnings.warn(message % args, warning, stacklevel=3)

rename_warning = generate_warning(
    "%r is deprecated and will be removed in astroid %.1f, use %r instead",
    PendingDeprecationWarning)

attribute_to_method_warning = generate_warning(
    "%s is deprecated and will be removed in astroid %.1f, use the "
    "method '%s()' instead.", PendingDeprecationWarning)

attribute_to_function_warning = generate_warning(
    "%s is deprecated and will be removed in astroid %.1f, use the "
    "function '%s()' instead.", PendingDeprecationWarning)

method_to_function_warning = generate_warning(
    "%s() is deprecated and will be removed in astroid %.1f, use the "
    "function '%s()' instead.", PendingDeprecationWarning)


class _Yes(object):
    """Special inference object, which is returned when inference fails."""
    def __repr__(self):
        return 'YES'

    __str__ = __repr__

    def __getattribute__(self, name):
        if name == 'next':
            raise AttributeError('next method should not be called')
        if name.startswith('__') and name.endswith('__'):
            return super(_Yes, self).__getattribute__(name)
        if name == 'accept':
            return super(_Yes, self).__getattribute__(name)
        return self

    def __call__(self, *args, **kwargs):
        return self

    def accept(self, visitor):
        func = getattr(visitor, "visit_yes")
        return func(self)


YES = _Yes()

def safe_infer(node, context=None):
    """Return the inferred value for the given node.

    Return None if inference failed or if there is some ambiguity (more than
    one node has been inferred).
    """
    try:
        inferit = node.infer(context=context)
        value = next(inferit)
    except exceptions.InferenceError:
        return
    try:
        next(inferit)
        return # None if there is ambiguity on the inferred node
    except exceptions.InferenceError:
        return # there is some kind of ambiguity
    except StopIteration:
        return value
