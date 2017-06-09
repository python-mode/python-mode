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
#
# The code in this file was originally part of logilab-common, licensed under
# the same license.

""" A few useful function/method decorators."""

import wrapt


@wrapt.decorator
def cached(func, instance, args, kwargs):
    """Simple decorator to cache result of method calls without args."""
    cache = getattr(instance, '__cache', None)
    if cache is None:
        instance.__cache = cache = {}
    try:
        return cache[func]
    except KeyError:
        cache[func] = result = func(*args, **kwargs)
        return result


class cachedproperty(object):
    """ Provides a cached property equivalent to the stacking of
    @cached and @property, but more efficient.

    After first usage, the <property_name> becomes part of the object's
    __dict__. Doing:

      del obj.<property_name> empties the cache.

    Idea taken from the pyramid_ framework and the mercurial_ project.

    .. _pyramid: http://pypi.python.org/pypi/pyramid
    .. _mercurial: http://pypi.python.org/pypi/Mercurial
    """
    __slots__ = ('wrapped',)

    def __init__(self, wrapped):
        try:
            wrapped.__name__
        except AttributeError:
            raise TypeError('%s must have a __name__ attribute' %
                            wrapped)
        self.wrapped = wrapped

    @property
    def __doc__(self):
        doc = getattr(self.wrapped, '__doc__', None)
        return ('<wrapped by the cachedproperty decorator>%s'
                % ('\n%s' % doc if doc else ''))

    def __get__(self, inst, objtype=None):
        if inst is None:
            return self
        val = self.wrapped(inst)
        setattr(inst, self.wrapped.__name__, val)
        return val
