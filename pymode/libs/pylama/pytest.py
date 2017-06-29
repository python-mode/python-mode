""" py.test plugin for checking files with pylama. """
from __future__ import absolute_import

from os import path as op

import py # noqa
import pytest


HISTKEY = "pylama/mtimes"


def pytest_addoption(parser):
    group = parser.getgroup("general")
    group.addoption(
        '--pylama', action='store_true',
        help="perform some pylama code checks on .py files")


def pytest_sessionstart(session):
    config = session.config
    if config.option.pylama and getattr(config, 'cache', None):
        config._pylamamtimes = config.cache.get(HISTKEY, {})


def pytest_sessionfinish(session):
    config = session.config
    if hasattr(config, "_pylamamtimes"):
        config.cache.set(HISTKEY, config._pylamamtimes)


def pytest_collect_file(path, parent):
    config = parent.config
    if config.option.pylama and path.ext == '.py':
        return PylamaItem(path, parent)


class PylamaError(Exception):
    """ indicates an error during pylama checks. """


class PylamaItem(pytest.Item, pytest.File):

    def __init__(self, path, parent):
        super(PylamaItem, self).__init__(path, parent)
        self.add_marker("pycodestyle")
        self.cache = None
        self._pylamamtimes = None

    def setup(self):
        if not getattr(self.config, 'cache', None):
            return False

        self.cache = True
        self._pylamamtimes = self.fspath.mtime()
        pylamamtimes = self.config._pylamamtimes
        old = pylamamtimes.get(str(self.fspath), 0)
        if old == self._pylamamtimes:
            pytest.skip("file(s) previously passed Pylama checks")

    def runtest(self):
        errors = check_file(self.fspath)
        if errors:
            pattern = "%(filename)s:%(lnum)s:%(col)s: %(text)s"
            out = "\n".join([pattern % e._info for e in errors])
            raise PylamaError(out)

        # update mtime only if test passed
        # otherwise failures would not be re-run next time
        if self.cache:
            self.config._pylamamtimes[str(self.fspath)] = self._pylamamtimes

    def repr_failure(self, excinfo):
        if excinfo.errisinstance(PylamaError):
            return excinfo.value.args[0]
        return super(PylamaItem, self).repr_failure(excinfo)


def check_file(path):
    from pylama.main import parse_options, process_paths
    from pylama.config import CURDIR

    options = parse_options()
    path = op.relpath(str(path), CURDIR)
    return process_paths(options, candidates=[path], error=False)

# pylama:ignore=D,E1002,W0212,F0001
