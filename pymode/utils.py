""" Pymode utils. """
import os.path
import sys
import threading
import warnings
from contextlib import contextmanager

import vim # noqa


try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


DEBUG = int(vim.eval('g:pymode_debug'))
PY2 = sys.version_info[0] == 2

warnings.filterwarnings('ignore')


@contextmanager
def silence_stderr():
    """ Redirect stderr. """

    if DEBUG:
        yield

    else:
        with threading.Lock():
            stderr = sys.stderr
            sys.stderr = StringIO()

        yield

        with threading.Lock():
            sys.stderr = stderr


def patch_paths():
    """ Function description. """

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'libs'))

    if PY2:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'libs2'))
    else:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'libs3'))
