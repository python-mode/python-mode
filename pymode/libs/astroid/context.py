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

"""Various context related utilities, including inference and call contexts."""

import contextlib


class InferenceContext(object):
    __slots__ = ('path', 'lookupname', 'callcontext', 'boundnode', 'inferred')

    def __init__(self, path=None, inferred=None):
        self.path = path or set()
        self.lookupname = None
        self.callcontext = None
        self.boundnode = None
        self.inferred = inferred or {}

    def push(self, node):
        name = self.lookupname
        if (node, name) in self.path:
            raise StopIteration()
        self.path.add((node, name))

    def clone(self):
        # XXX copy lookupname/callcontext ?
        clone = InferenceContext(self.path, inferred=self.inferred)
        clone.callcontext = self.callcontext
        clone.boundnode = self.boundnode
        return clone

    def cache_generator(self, key, generator):
        results = []
        for result in generator:
            results.append(result)
            yield result

        self.inferred[key] = tuple(results)
        return

    @contextlib.contextmanager
    def restore_path(self):
        path = set(self.path)
        yield
        self.path = path


class CallContext(object):
    """Holds information for a call site."""

    __slots__ = ('args', 'keywords')

    def __init__(self, args, keywords=None):
        self.args = args
        if keywords:
            keywords = [(arg.arg, arg.value) for arg in keywords]
        else:
            keywords = []
        self.keywords = keywords


def copy_context(context):
    if context is not None:
        return context.clone()
    else:
        return InferenceContext()
