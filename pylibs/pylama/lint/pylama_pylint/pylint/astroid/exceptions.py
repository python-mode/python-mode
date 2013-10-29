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
"""this module contains exceptions used in the astroid library

"""

__doctype__ = "restructuredtext en"

class AstroidError(Exception):
    """base exception class for all astroid related exceptions"""

class AstroidBuildingException(AstroidError):
    """exception class when we are unable to build an astroid representation"""

class ResolveError(AstroidError):
    """base class of astroid resolution/inference error"""

class NotFoundError(ResolveError):
    """raised when we are unable to resolve a name"""

class InferenceError(ResolveError):
    """raised when we are unable to infer a node"""

class UseInferenceDefault(Exception):
    """exception to be raised in custom inference function to indicate that it
    should go back to the default behaviour
    """

class UnresolvableName(InferenceError):
    """raised when we are unable to resolve a name"""

class NoDefault(AstroidError):
    """raised by function's `default_value` method when an argument has
    no default value
    """

