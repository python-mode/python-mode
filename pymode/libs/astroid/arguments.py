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

from astroid import bases
from astroid import context as contextmod
from astroid import exceptions
from astroid import nodes
from astroid import util

import six


class CallSite(object):
    """Class for understanding arguments passed into a call site

    It needs a call context, which contains the arguments and the
    keyword arguments that were passed into a given call site.
    In order to infer what an argument represents, call
    :meth:`infer_argument` with the corresponding function node
    and the argument name.
    """

    def __init__(self, callcontext):
        args = callcontext.args
        keywords = callcontext.keywords
        self.duplicated_keywords = set()
        self._unpacked_args = self._unpack_args(args)
        self._unpacked_kwargs = self._unpack_keywords(keywords)

        self.positional_arguments = [
            arg for arg in self._unpacked_args
            if arg is not util.YES
        ]
        self.keyword_arguments = {
            key: value for key, value in self._unpacked_kwargs.items()
            if value is not util.YES
        }

    @classmethod
    def from_call(cls, call_node):
        """Get a CallSite object from the given Call node."""
        callcontext = contextmod.CallContext(call_node.args,
                                             call_node.keywords)
        return cls(callcontext)

    def has_invalid_arguments(self):
        """Check if in the current CallSite were passed *invalid* arguments

        This can mean multiple things. For instance, if an unpacking
        of an invalid object was passed, then this method will return True.
        Other cases can be when the arguments can't be inferred by astroid,
        for example, by passing objects which aren't known statically.
        """
        return len(self.positional_arguments) != len(self._unpacked_args)

    def has_invalid_keywords(self):
        """Check if in the current CallSite were passed *invalid* keyword arguments

        For instance, unpacking a dictionary with integer keys is invalid
        (**{1:2}), because the keys must be strings, which will make this
        method to return True. Other cases where this might return True if
        objects which can't be inferred were passed.
        """
        return len(self.keyword_arguments) != len(self._unpacked_kwargs)

    def _unpack_keywords(self, keywords):
        values = {}
        context = contextmod.InferenceContext()
        for name, value in keywords:
            if name is None:
                # Then it's an unpacking operation (**)
                try:
                    inferred = next(value.infer(context=context))
                except exceptions.InferenceError:
                    values[name] = util.YES
                    continue

                if not isinstance(inferred, nodes.Dict):
                    # Not something we can work with.
                    values[name] = util.YES
                    continue

                for dict_key, dict_value in inferred.items:
                    try:
                        dict_key = next(dict_key.infer(context=context))
                    except exceptions.InferenceError:
                        values[name] = util.YES
                        continue
                    if not isinstance(dict_key, nodes.Const):
                        values[name] = util.YES
                        continue
                    if not isinstance(dict_key.value, six.string_types):
                        values[name] = util.YES
                        continue
                    if dict_key.value in values:
                        # The name is already in the dictionary
                        values[dict_key.value] = util.YES
                        self.duplicated_keywords.add(dict_key.value)
                        continue
                    values[dict_key.value] = dict_value
            else:
                values[name] = value
        return values

    @staticmethod
    def _unpack_args(args):
        values = []
        context = contextmod.InferenceContext()
        for arg in args:
            if isinstance(arg, nodes.Starred):
                try:
                    inferred = next(arg.value.infer(context=context))
                except exceptions.InferenceError:
                    values.append(util.YES)
                    continue

                if inferred is util.YES:
                    values.append(util.YES)
                    continue
                if not hasattr(inferred, 'elts'):
                    values.append(util.YES)
                    continue
                values.extend(inferred.elts)
            else:
                values.append(arg)
        return values

    def infer_argument(self, funcnode, name, context):
        """infer a function argument value according to the call context"""
        if name in self.duplicated_keywords:
            raise exceptions.InferenceError(name)

        # Look into the keywords first, maybe it's already there.
        try:
            return self.keyword_arguments[name].infer(context)
        except KeyError:
            pass

        # Too many arguments given and no variable arguments.
        if len(self.positional_arguments) > len(funcnode.args.args):
            if not funcnode.args.vararg:
                raise exceptions.InferenceError(name)

        positional = self.positional_arguments[:len(funcnode.args.args)]
        vararg = self.positional_arguments[len(funcnode.args.args):]
        argindex = funcnode.args.find_argname(name)[0]
        kwonlyargs = set(arg.name for arg in funcnode.args.kwonlyargs)
        kwargs = {
            key: value for key, value in self.keyword_arguments.items()
            if key not in kwonlyargs
        }
        # If there are too few positionals compared to
        # what the function expects to receive, check to see
        # if the missing positional arguments were passed
        # as keyword arguments and if so, place them into the
        # positional args list.
        if len(positional) < len(funcnode.args.args):
            for func_arg in funcnode.args.args:
                if func_arg.name in kwargs:
                    arg = kwargs.pop(func_arg.name)
                    positional.append(arg)

        if argindex is not None:
            # 2. first argument of instance/class method
            if argindex == 0 and funcnode.type in ('method', 'classmethod'):
                if context.boundnode is not None:
                    boundnode = context.boundnode
                else:
                    # XXX can do better ?
                    boundnode = funcnode.parent.frame()
                if funcnode.type == 'method':
                    if not isinstance(boundnode, bases.Instance):
                        boundnode = bases.Instance(boundnode)
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
                return self.positional_arguments[argindex].infer(context)
            except IndexError:
                pass

        if funcnode.args.kwarg == name:
            # It wants all the keywords that were passed into
            # the call site.
            if self.has_invalid_keywords():
                raise exceptions.InferenceError
            kwarg = nodes.Dict()
            kwarg.lineno = funcnode.args.lineno
            kwarg.col_offset = funcnode.args.col_offset
            kwarg.parent = funcnode.args
            items = [(nodes.const_factory(key), value)
                     for key, value in kwargs.items()]
            kwarg.items = items
            return iter((kwarg, ))
        elif funcnode.args.vararg == name:
            # It wants all the args that were passed into
            # the call site.
            if self.has_invalid_arguments():
                raise exceptions.InferenceError
            args = nodes.Tuple()
            args.lineno = funcnode.args.lineno
            args.col_offset = funcnode.args.col_offset
            args.parent = funcnode.args
            args.elts = vararg
            return iter((args, ))

        # Check if it's a default parameter.
        try:
            return funcnode.args.default_value(name).infer(context)
        except exceptions.NoDefault:
            pass
        raise exceptions.InferenceError(name)
