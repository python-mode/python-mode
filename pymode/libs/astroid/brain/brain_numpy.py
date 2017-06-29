# copyright 2003-2015 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
# contact http://www.logilab.fr/ -- mailto:contact@logilab.fr
#
# This file is part of astroid.
#
# astroid is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 2.1 of the License, or (at your option) any
# later version.
#
# astroid is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with astroid.  If not, see <http://www.gnu.org/licenses/>.

"""Astroid hooks for numpy."""

import astroid


# TODO(cpopa): drop when understanding augmented assignments

def numpy_core_transform():
    return astroid.parse('''
    from numpy.core import numeric
    from numpy.core import fromnumeric
    from numpy.core import defchararray
    from numpy.core import records
    from numpy.core import function_base
    from numpy.core import machar
    from numpy.core import getlimits
    from numpy.core import shape_base
    __all__ = (['char', 'rec', 'memmap', 'chararray'] + numeric.__all__ +
               fromnumeric.__all__ +
               records.__all__ +
               function_base.__all__ +
               machar.__all__ +
               getlimits.__all__ +
               shape_base.__all__)
    ''')


def numpy_transform():
    return astroid.parse('''
    from numpy import core
    from numpy import matrixlib as _mat
    from numpy import lib
    __all__ = ['add_newdocs',
               'ModuleDeprecationWarning',
               'VisibleDeprecationWarning', 'linalg', 'fft', 'random',
               'ctypeslib', 'ma',
               '__version__', 'pkgload', 'PackageLoader',
               'show_config'] + core.__all__ + _mat.__all__ + lib.__all__

    ''')
    

astroid.register_module_extender(astroid.MANAGER, 'numpy.core', numpy_core_transform)
astroid.register_module_extender(astroid.MANAGER, 'numpy', numpy_transform)
