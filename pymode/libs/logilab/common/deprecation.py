# copyright 2003-2012 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
# contact http://www.logilab.fr/ -- mailto:contact@logilab.fr
#
# This file is part of logilab-common.
#
# logilab-common is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 2.1 of the License, or (at your option) any
# later version.
#
# logilab-common is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with logilab-common.  If not, see <http://www.gnu.org/licenses/>.
"""Deprecation utilities."""

__docformat__ = "restructuredtext en"

import sys
from warnings import warn

from logilab.common.changelog import Version


class DeprecationWrapper(object):
    """proxy to print a warning on access to any attribute of the wrapped object
    """
    def __init__(self, proxied, msg=None):
        self._proxied = proxied
        self._msg = msg

    def __getattr__(self, attr):
        warn(self._msg, DeprecationWarning, stacklevel=2)
        return getattr(self._proxied, attr)

    def __setattr__(self, attr, value):
        if attr in ('_proxied', '_msg'):
            self.__dict__[attr] = value
        else:
            warn(self._msg, DeprecationWarning, stacklevel=2)
            setattr(self._proxied, attr, value)


class DeprecationManager(object):
    """Manage the deprecation message handling. Messages are dropped for
    versions more recent than the 'compatible' version. Example::

        deprecator = deprecation.DeprecationManager("module_name")
        deprecator.compatibility('1.3')

        deprecator.warn('1.2', "message.")

        @deprecator.deprecated('1.2', 'Message')
        def any_func():
            pass

        class AnyClass(object):
            __metaclass__ = deprecator.class_deprecated('1.2')
    """
    def __init__(self, module_name=None):
        """
        """
        self.module_name = module_name
        self.compatible_version = None

    def compatibility(self, compatible_version):
        """Set the compatible version.
        """
        self.compatible_version = Version(compatible_version)

    def deprecated(self, version=None, reason=None, stacklevel=2, name=None, doc=None):
        """Display a deprecation message only if the version is older than the
        compatible version.
        """
        def decorator(func):
            message = reason or 'The function "%s" is deprecated'
            if '%s' in message:
                message %= func.__name__
            def wrapped(*args, **kwargs):
                self.warn(version, message, stacklevel+1)
                return func(*args, **kwargs)
            return wrapped
        return decorator

    def class_deprecated(self, version=None):
        class metaclass(type):
            """metaclass to print a warning on instantiation of a deprecated class"""

            def __call__(cls, *args, **kwargs):
                msg = getattr(cls, "__deprecation_warning__",
                              "%(cls)s is deprecated") % {'cls': cls.__name__}
                self.warn(version, msg, stacklevel=3)
                return type.__call__(cls, *args, **kwargs)
        return metaclass

    def moved(self, version, modpath, objname):
        """use to tell that a callable has been moved to a new module.

        It returns a callable wrapper, so that when its called a warning is printed
        telling where the object can be found, import is done (and not before) and
        the actual object is called.

        NOTE: the usage is somewhat limited on classes since it will fail if the
        wrapper is use in a class ancestors list, use the `class_moved` function
        instead (which has no lazy import feature though).
        """
        def callnew(*args, **kwargs):
            from logilab.common.modutils import load_module_from_name
            message = "object %s has been moved to module %s" % (objname, modpath)
            self.warn(version, message)
            m = load_module_from_name(modpath)
            return getattr(m, objname)(*args, **kwargs)
        return callnew

    def class_renamed(self, version, old_name, new_class, message=None):
        clsdict = {}
        if message is None:
            message = '%s is deprecated, use %s' % (old_name, new_class.__name__)
        clsdict['__deprecation_warning__'] = message
        try:
            # new-style class
            return self.class_deprecated(version)(old_name, (new_class,), clsdict)
        except (NameError, TypeError):
            # old-style class
            warn = self.warn
            class DeprecatedClass(new_class):
                """FIXME: There might be a better way to handle old/new-style class
                """
                def __init__(self, *args, **kwargs):
                    warn(version, message, stacklevel=3)
                    new_class.__init__(self, *args, **kwargs)
            return DeprecatedClass

    def class_moved(self, version, new_class, old_name=None, message=None):
        """nice wrapper around class_renamed when a class has been moved into
        another module
        """
        if old_name is None:
            old_name = new_class.__name__
        if message is None:
            message = 'class %s is now available as %s.%s' % (
                old_name, new_class.__module__, new_class.__name__)
        return self.class_renamed(version, old_name, new_class, message)

    def warn(self, version=None, reason="", stacklevel=2):
        """Display a deprecation message only if the version is older than the
        compatible version.
        """
        if (self.compatible_version is None
            or version is None
            or Version(version) < self.compatible_version):
            if self.module_name and version:
                reason = '[%s %s] %s' % (self.module_name, version, reason)
            elif self.module_name:
                reason = '[%s] %s' % (self.module_name, reason)
            elif version:
                reason = '[%s] %s' % (version, reason)
            warn(reason, DeprecationWarning, stacklevel=stacklevel)

_defaultdeprecator = DeprecationManager()

def deprecated(reason=None, stacklevel=2, name=None, doc=None):
    return _defaultdeprecator.deprecated(None, reason, stacklevel, name, doc)

class_deprecated = _defaultdeprecator.class_deprecated()

def moved(modpath, objname):
    return _defaultdeprecator.moved(None, modpath, objname)
moved.__doc__ = _defaultdeprecator.moved.__doc__

def class_renamed(old_name, new_class, message=None):
    """automatically creates a class which fires a DeprecationWarning
    when instantiated.

    >>> Set = class_renamed('Set', set, 'Set is now replaced by set')
    >>> s = Set()
    sample.py:57: DeprecationWarning: Set is now replaced by set
    s = Set()
    >>>
    """
    return _defaultdeprecator.class_renamed(None, old_name, new_class, message)

def class_moved(new_class, old_name=None, message=None):
    return _defaultdeprecator.class_moved(None, new_class, old_name, message)
class_moved.__doc__ = _defaultdeprecator.class_moved.__doc__

