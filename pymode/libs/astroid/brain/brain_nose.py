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

"""Hooks for nose library."""

import re
import textwrap

import astroid
import astroid.builder

_BUILDER = astroid.builder.AstroidBuilder(astroid.MANAGER)


def _pep8(name, caps=re.compile('([A-Z])')):
    return caps.sub(lambda m: '_' + m.groups()[0].lower(), name)


def _nose_tools_functions():
    """Get an iterator of names and bound methods."""
    module = _BUILDER.string_build(textwrap.dedent('''
    import unittest

    class Test(unittest.TestCase):
        pass
    a = Test()
    '''))
    try:
        case = next(module['a'].infer())
    except astroid.InferenceError:
        return
    for method in case.methods():
        if method.name.startswith('assert') and '_' not in method.name:
            pep8_name = _pep8(method.name)
            yield pep8_name, astroid.BoundMethod(method, case)
        if method.name == 'assertEqual':
            # nose also exports assert_equals.
            yield 'assert_equals', astroid.BoundMethod(method, case)


def _nose_tools_transform(node):
    for method_name, method in _nose_tools_functions():
        node._locals[method_name] = [method]


def _nose_tools_trivial_transform():
    """Custom transform for the nose.tools module."""
    stub = _BUILDER.string_build('''__all__ = []''')
    all_entries = ['ok_', 'eq_']

    for pep8_name, method in _nose_tools_functions():
        all_entries.append(pep8_name)
        stub[pep8_name] = method

    # Update the __all__ variable, since nose.tools
    # does this manually with .append.
    all_assign = stub['__all__'].parent
    all_object = astroid.List(all_entries)
    all_object.parent = all_assign
    all_assign.value = all_object
    return stub


astroid.register_module_extender(astroid.MANAGER, 'nose.tools.trivial',
                                 _nose_tools_trivial_transform)
astroid.MANAGER.register_transform(astroid.Module, _nose_tools_transform,
                                   lambda n: n.name == 'nose.tools')
