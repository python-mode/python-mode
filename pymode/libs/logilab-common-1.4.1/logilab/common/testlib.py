# -*- coding: utf-8 -*-
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
"""Run tests.

This will find all modules whose name match a given prefix in the test
directory, and run them. Various command line options provide
additional facilities.

Command line options:

 -v  verbose -- run tests in verbose mode with output to stdout
 -q  quiet   -- don't print anything except if a test fails
 -t  testdir -- directory where the tests will be found
 -x  exclude -- add a test to exclude
 -p  profile -- profiled execution
 -d  dbc     -- enable design-by-contract
 -m  match   -- only run test matching the tag pattern which follow

If no non-option arguments are present, prefixes used are 'test',
'regrtest', 'smoketest' and 'unittest'.

"""

from __future__ import print_function

__docformat__ = "restructuredtext en"
# modified copy of some functions from test/regrtest.py from PyXml
# disable camel case warning
# pylint: disable=C0103

from contextlib import contextmanager
import sys
import os, os.path as osp
import re
import difflib
import tempfile
import math
import warnings
from shutil import rmtree
from operator import itemgetter
from inspect import isgeneratorfunction

from six import PY2, add_metaclass, string_types
from six.moves import builtins, range, configparser, input

from logilab.common.deprecation import class_deprecated, deprecated

import unittest as unittest_legacy
if not getattr(unittest_legacy, "__package__", None):
    try:
        import unittest2 as unittest
        from unittest2 import SkipTest
    except ImportError:
        raise ImportError("You have to install python-unittest2 to use %s" % __name__)
else:
    import unittest as unittest
    from unittest import SkipTest

from functools import wraps

from logilab.common.debugger import Debugger
from logilab.common.decorators import cached, classproperty
from logilab.common import textutils


__all__ = ['unittest_main', 'find_tests', 'nocoverage', 'pause_trace']

DEFAULT_PREFIXES = ('test', 'regrtest', 'smoketest', 'unittest',
                    'func', 'validation')

is_generator = deprecated('[lgc 0.63] use inspect.isgeneratorfunction')(isgeneratorfunction)

# used by unittest to count the number of relevant levels in the traceback
__unittest = 1


@deprecated('with_tempdir is deprecated, use {0}.TemporaryDirectory.'.format(
    'tempfile' if not PY2 else 'backports.tempfile'))
def with_tempdir(callable):
    """A decorator ensuring no temporary file left when the function return
    Work only for temporary file created with the tempfile module"""
    if isgeneratorfunction(callable):
        def proxy(*args, **kwargs):
            old_tmpdir = tempfile.gettempdir()
            new_tmpdir = tempfile.mkdtemp(prefix="temp-lgc-")
            tempfile.tempdir = new_tmpdir
            try:
                for x in callable(*args, **kwargs):
                    yield x
            finally:
                try:
                    rmtree(new_tmpdir, ignore_errors=True)
                finally:
                    tempfile.tempdir = old_tmpdir
        return proxy

    @wraps(callable)
    def proxy(*args, **kargs):

        old_tmpdir = tempfile.gettempdir()
        new_tmpdir = tempfile.mkdtemp(prefix="temp-lgc-")
        tempfile.tempdir = new_tmpdir
        try:
            return callable(*args, **kargs)
        finally:
            try:
                rmtree(new_tmpdir, ignore_errors=True)
            finally:
                tempfile.tempdir = old_tmpdir
    return proxy

def in_tempdir(callable):
    """A decorator moving the enclosed function inside the tempfile.tempfdir
    """
    @wraps(callable)
    def proxy(*args, **kargs):

        old_cwd = os.getcwd()
        os.chdir(tempfile.tempdir)
        try:
            return callable(*args, **kargs)
        finally:
            os.chdir(old_cwd)
    return proxy

def within_tempdir(callable):
    """A decorator run the enclosed function inside a tmpdir removed after execution
    """
    proxy = with_tempdir(in_tempdir(callable))
    proxy.__name__ = callable.__name__
    return proxy

def find_tests(testdir,
               prefixes=DEFAULT_PREFIXES, suffix=".py",
               excludes=(),
               remove_suffix=True):
    """
    Return a list of all applicable test modules.
    """
    tests = []
    for name in os.listdir(testdir):
        if not suffix or name.endswith(suffix):
            for prefix in prefixes:
                if name.startswith(prefix):
                    if remove_suffix and name.endswith(suffix):
                        name = name[:-len(suffix)]
                    if name not in excludes:
                        tests.append(name)
    tests.sort()
    return tests


## PostMortem Debug facilities #####
def start_interactive_mode(result):
    """starts an interactive shell so that the user can inspect errors
    """
    debuggers = result.debuggers
    descrs = result.error_descrs + result.fail_descrs
    if len(debuggers) == 1:
        # don't ask for test name if there's only one failure
        debuggers[0].start()
    else:
        while True:
            testindex = 0
            print("Choose a test to debug:")
            # order debuggers in the same way than errors were printed
            print("\n".join(['\t%s : %s' % (i, descr) for i, (_, descr)
                  in enumerate(descrs)]))
            print("Type 'exit' (or ^D) to quit")
            print()
            try:
                todebug = input('Enter a test name: ')
                if todebug.strip().lower() == 'exit':
                    print()
                    break
                else:
                    try:
                        testindex = int(todebug)
                        debugger = debuggers[descrs[testindex][0]]
                    except (ValueError, IndexError):
                        print("ERROR: invalid test number %r" % (todebug, ))
                    else:
                        debugger.start()
            except (EOFError, KeyboardInterrupt):
                print()
                break


# coverage pausing tools #####################################################

@contextmanager
def replace_trace(trace=None):
    """A context manager that temporary replaces the trace function"""
    oldtrace = sys.gettrace()
    sys.settrace(trace)
    try:
        yield
    finally:
        # specific hack to work around a bug in pycoverage, see
        # https://bitbucket.org/ned/coveragepy/issue/123
        if (oldtrace is not None and not callable(oldtrace) and
            hasattr(oldtrace, 'pytrace')):
            oldtrace = oldtrace.pytrace
        sys.settrace(oldtrace)


pause_trace = replace_trace


def nocoverage(func):
    """Function decorator that pauses tracing functions"""
    if hasattr(func, 'uncovered'):
        return func
    func.uncovered = True

    def not_covered(*args, **kwargs):
        with pause_trace():
            return func(*args, **kwargs)
    not_covered.uncovered = True
    return not_covered


# test utils ##################################################################


# Add deprecation warnings about new api used by module level fixtures in unittest2
# http://www.voidspace.org.uk/python/articles/unittest2.shtml#setupmodule-and-teardownmodule
class _DebugResult(object): # simplify import statement among unittest flavors..
    "Used by the TestSuite to hold previous class when running in debug."
    _previousTestClass = None
    _moduleSetUpFailed = False
    shouldStop = False

# backward compatibility: TestSuite might be imported from lgc.testlib
TestSuite = unittest.TestSuite

class keywords(dict):
    """Keyword args (**kwargs) support for generative tests."""

class starargs(tuple):
    """Variable arguments (*args) for generative tests."""
    def __new__(cls, *args):
        return tuple.__new__(cls, args)

unittest_main = unittest.main


class InnerTestSkipped(SkipTest):
    """raised when a test is skipped"""
    pass

def parse_generative_args(params):
    args = []
    varargs = ()
    kwargs = {}
    flags = 0 # 2 <=> starargs, 4 <=> kwargs
    for param in params:
        if isinstance(param, starargs):
            varargs = param
            if flags:
                raise TypeError('found starargs after keywords !')
            flags |= 2
            args += list(varargs)
        elif isinstance(param, keywords):
            kwargs = param
            if flags & 4:
                raise TypeError('got multiple keywords parameters')
            flags |= 4
        elif flags & 2 or flags & 4:
            raise TypeError('found parameters after kwargs or args')
        else:
            args.append(param)

    return args, kwargs


class InnerTest(tuple):
    def __new__(cls, name, *data):
        instance = tuple.__new__(cls, data)
        instance.name = name
        return instance

class Tags(set):
    """A set of tag able validate an expression"""

    def __init__(self, *tags, **kwargs):
        self.inherit = kwargs.pop('inherit', True)
        if kwargs:
           raise TypeError("%s are an invalid keyword argument for this function" % kwargs.keys())

        if len(tags) == 1 and not isinstance(tags[0], string_types):
            tags = tags[0]
        super(Tags, self).__init__(tags, **kwargs)

    def __getitem__(self, key):
        return key in self

    def match(self, exp):
        return eval(exp, {}, self)

    def __or__(self, other):
        return Tags(*super(Tags, self).__or__(other))


# duplicate definition from unittest2 of the _deprecate decorator
def _deprecate(original_func):
    def deprecated_func(*args, **kwargs):
        warnings.warn(
            ('Please use %s instead.' % original_func.__name__),
            DeprecationWarning, 2)
        return original_func(*args, **kwargs)
    return deprecated_func

class TestCase(unittest.TestCase):
    """A unittest.TestCase extension with some additional methods."""
    maxDiff = None
    tags = Tags()

    def __init__(self, methodName='runTest'):
        super(TestCase, self).__init__(methodName)
        self.__exc_info = sys.exc_info
        self.__testMethodName = self._testMethodName
        self._current_test_descr = None
        self._options_ = None

    @classproperty
    @cached
    def datadir(cls): # pylint: disable=E0213
        """helper attribute holding the standard test's data directory

        NOTE: this is a logilab's standard
        """
        mod = sys.modules[cls.__module__]
        return osp.join(osp.dirname(osp.abspath(mod.__file__)), 'data')
    # cache it (use a class method to cache on class since TestCase is
    # instantiated for each test run)

    @classmethod
    def datapath(cls, *fname):
        """joins the object's datadir and `fname`"""
        return osp.join(cls.datadir, *fname)

    def set_description(self, descr):
        """sets the current test's description.
        This can be useful for generative tests because it allows to specify
        a description per yield
        """
        self._current_test_descr = descr

    # override default's unittest.py feature
    def shortDescription(self):
        """override default unittest shortDescription to handle correctly
        generative tests
        """
        if self._current_test_descr is not None:
            return self._current_test_descr
        return super(TestCase, self).shortDescription()

    def quiet_run(self, result, func, *args, **kwargs):
        try:
            func(*args, **kwargs)
        except (KeyboardInterrupt, SystemExit):
            raise
        except unittest.SkipTest as e:
            if hasattr(result, 'addSkip'):
                result.addSkip(self, str(e))
            else:
                warnings.warn("TestResult has no addSkip method, skips not reported",
                              RuntimeWarning, 2)
                result.addSuccess(self)
            return False
        except:
            result.addError(self, self.__exc_info())
            return False
        return True

    def _get_test_method(self):
        """return the test method"""
        return getattr(self, self._testMethodName)

    def optval(self, option, default=None):
        """return the option value or default if the option is not define"""
        return getattr(self._options_, option, default)

    def __call__(self, result=None, runcondition=None, options=None):
        """rewrite TestCase.__call__ to support generative tests
        This is mostly a copy/paste from unittest.py (i.e same
        variable names, same logic, except for the generative tests part)
        """
        if result is None:
            result = self.defaultTestResult()
        self._options_ = options
        # if result.cvg:
        #     result.cvg.start()
        testMethod = self._get_test_method()
        if (getattr(self.__class__, "__unittest_skip__", False) or
            getattr(testMethod, "__unittest_skip__", False)):
            # If the class or method was skipped.
            try:
                skip_why = (getattr(self.__class__, '__unittest_skip_why__', '')
                            or getattr(testMethod, '__unittest_skip_why__', ''))
                if hasattr(result, 'addSkip'):
                    result.addSkip(self, skip_why)
                else:
                    warnings.warn("TestResult has no addSkip method, skips not reported",
                                  RuntimeWarning, 2)
                    result.addSuccess(self)
            finally:
                result.stopTest(self)
            return
        if runcondition and not runcondition(testMethod):
            return # test is skipped
        result.startTest(self)
        try:
            if not self.quiet_run(result, self.setUp):
                return
            generative = isgeneratorfunction(testMethod)
            # generative tests
            if generative:
                self._proceed_generative(result, testMethod,
                                         runcondition)
            else:
                status = self._proceed(result, testMethod)
                success = (status == 0)
            if not self.quiet_run(result, self.tearDown):
                return
            if not generative and success:
                result.addSuccess(self)
        finally:
            # if result.cvg:
            #     result.cvg.stop()
            result.stopTest(self)

    def _proceed_generative(self, result, testfunc, runcondition=None):
        # cancel startTest()'s increment
        result.testsRun -= 1
        success = True
        try:
            for params in testfunc():
                if runcondition and not runcondition(testfunc,
                        skipgenerator=False):
                    if not (isinstance(params, InnerTest)
                            and runcondition(params)):
                        continue
                if not isinstance(params, (tuple, list)):
                    params = (params, )
                func = params[0]
                args, kwargs = parse_generative_args(params[1:])
                # increment test counter manually
                result.testsRun += 1
                status = self._proceed(result, func, args, kwargs)
                if status == 0:
                    result.addSuccess(self)
                    success = True
                else:
                    success = False
                    # XXX Don't stop anymore if an error occured
                    #if status == 2:
                    #    result.shouldStop = True
                if result.shouldStop: # either on error or on exitfirst + error
                    break
        except self.failureException:
            result.addFailure(self, self.__exc_info())
            success = False
        except SkipTest as e:
            result.addSkip(self, e)
        except:
            # if an error occurs between two yield
            result.addError(self, self.__exc_info())
            success = False
        return success

    def _proceed(self, result, testfunc, args=(), kwargs=None):
        """proceed the actual test
        returns 0 on success, 1 on failure, 2 on error

        Note: addSuccess can't be called here because we have to wait
        for tearDown to be successfully executed to declare the test as
        successful
        """
        kwargs = kwargs or {}
        try:
            testfunc(*args, **kwargs)
        except self.failureException:
            result.addFailure(self, self.__exc_info())
            return 1
        except KeyboardInterrupt:
            raise
        except InnerTestSkipped as e:
            result.addSkip(self, e)
            return 1
        except SkipTest as e:
            result.addSkip(self, e)
            return 0
        except:
            result.addError(self, self.__exc_info())
            return 2
        return 0

    def innerSkip(self, msg=None):
        """mark a generative test as skipped for the <msg> reason"""
        msg = msg or 'test was skipped'
        raise InnerTestSkipped(msg)

    if sys.version_info >= (3,2):
        assertItemsEqual = unittest.TestCase.assertCountEqual
    else:
        assertCountEqual = unittest.TestCase.assertItemsEqual

TestCase.assertItemsEqual = deprecated('assertItemsEqual is deprecated, use assertCountEqual')(
    TestCase.assertItemsEqual)

import doctest

class SkippedSuite(unittest.TestSuite):
    def test(self):
        """just there to trigger test execution"""
        self.skipped_test('doctest module has no DocTestSuite class')


class DocTestFinder(doctest.DocTestFinder):

    def __init__(self, *args, **kwargs):
        self.skipped = kwargs.pop('skipped', ())
        doctest.DocTestFinder.__init__(self, *args, **kwargs)

    def _get_test(self, obj, name, module, globs, source_lines):
        """override default _get_test method to be able to skip tests
        according to skipped attribute's value
        """
        if getattr(obj, '__name__', '') in self.skipped:
            return None
        return doctest.DocTestFinder._get_test(self, obj, name, module,
                                               globs, source_lines)


@add_metaclass(class_deprecated)
class DocTest(TestCase):
    """trigger module doctest
    I don't know how to make unittest.main consider the DocTestSuite instance
    without this hack
    """
    __deprecation_warning__ = 'use stdlib doctest module with unittest API directly'
    skipped = ()
    def __call__(self, result=None, runcondition=None, options=None):\
        # pylint: disable=W0613
        try:
            finder = DocTestFinder(skipped=self.skipped)
            suite = doctest.DocTestSuite(self.module, test_finder=finder)
            # XXX iirk
            doctest.DocTestCase._TestCase__exc_info = sys.exc_info
        except AttributeError:
            suite = SkippedSuite()
        # doctest may gork the builtins dictionnary
        # This happen to the "_" entry used by gettext
        old_builtins = builtins.__dict__.copy()
        try:
            return suite.run(result)
        finally:
            builtins.__dict__.clear()
            builtins.__dict__.update(old_builtins)
    run = __call__

    def test(self):
        """just there to trigger test execution"""


class MockConnection:
    """fake DB-API 2.0 connexion AND cursor (i.e. cursor() return self)"""

    def __init__(self, results):
        self.received = []
        self.states = []
        self.results = results

    def cursor(self):
        """Mock cursor method"""
        return self
    def execute(self, query, args=None):
        """Mock execute method"""
        self.received.append( (query, args) )
    def fetchone(self):
        """Mock fetchone method"""
        return self.results[0]
    def fetchall(self):
        """Mock fetchall method"""
        return self.results
    def commit(self):
        """Mock commiy method"""
        self.states.append( ('commit', len(self.received)) )
    def rollback(self):
        """Mock rollback method"""
        self.states.append( ('rollback', len(self.received)) )
    def close(self):
        """Mock close method"""
        pass


def mock_object(**params):
    """creates an object using params to set attributes
    >>> option = mock_object(verbose=False, index=range(5))
    >>> option.verbose
    False
    >>> option.index
    [0, 1, 2, 3, 4]
    """
    return type('Mock', (), params)()


def create_files(paths, chroot):
    """Creates directories and files found in <path>.

    :param paths: list of relative paths to files or directories
    :param chroot: the root directory in which paths will be created

    >>> from os.path import isdir, isfile
    >>> isdir('/tmp/a')
    False
    >>> create_files(['a/b/foo.py', 'a/b/c/', 'a/b/c/d/e.py'], '/tmp')
    >>> isdir('/tmp/a')
    True
    >>> isdir('/tmp/a/b/c')
    True
    >>> isfile('/tmp/a/b/c/d/e.py')
    True
    >>> isfile('/tmp/a/b/foo.py')
    True
    """
    dirs, files = set(), set()
    for path in paths:
        path = osp.join(chroot, path)
        filename = osp.basename(path)
        # path is a directory path
        if filename == '':
            dirs.add(path)
        # path is a filename path
        else:
            dirs.add(osp.dirname(path))
            files.add(path)
    for dirpath in dirs:
        if not osp.isdir(dirpath):
            os.makedirs(dirpath)
    for filepath in files:
        open(filepath, 'w').close()


class AttrObject: # XXX cf mock_object
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

def tag(*args, **kwargs):
    """descriptor adding tag to a function"""
    def desc(func):
        assert not hasattr(func, 'tags')
        func.tags = Tags(*args, **kwargs)
        return func
    return desc

def require_version(version):
    """ Compare version of python interpreter to the given one. Skip the test
    if older.
    """
    def check_require_version(f):
        version_elements = version.split('.')
        try:
            compare = tuple([int(v) for v in version_elements])
        except ValueError:
            raise ValueError('%s is not a correct version : should be X.Y[.Z].' % version)
        current = sys.version_info[:3]
        if current < compare:
            def new_f(self, *args, **kwargs):
                self.skipTest('Need at least %s version of python. Current version is %s.' % (version, '.'.join([str(element) for element in current])))
            new_f.__name__ = f.__name__
            return new_f
        else:
            return f
    return check_require_version

def require_module(module):
    """ Check if the given module is loaded. Skip the test if not.
    """
    def check_require_module(f):
        try:
            __import__(module)
            return f
        except ImportError:
            def new_f(self, *args, **kwargs):
                self.skipTest('%s can not be imported.' % module)
            new_f.__name__ = f.__name__
            return new_f
    return check_require_module

