""" Pymode utils. """
import os.path
import sys
import threading
import warnings
from contextlib import contextmanager

import vim # noqa
from ._compat import StringIO


DEBUG = int(vim.eval('g:pymode_debug'))

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
    """Patch python sys.path.

    Load required modules from the plugin's sources.
    """
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'libs'))
