"""Pymode utils."""
import os.path
import sys
import threading
import warnings
from contextlib import contextmanager
from io import StringIO

import vim  # noqa


DEBUG = int(vim.eval('g:pymode_debug'))

warnings.filterwarnings('ignore')


@contextmanager
def silence_stderr():
    """Redirect stderr."""
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
    dir_script = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.join(dir_script, 'libs'))
    if sys.platform == 'win32' or sys.platform == 'msys':
        dir_submodule = os.path.abspath(os.path.join(dir_script,
                                                     '..', 'submodules'))
        # Only add submodules that are still needed
        # Required: rope (IDE features), tomli (rope dependency via pytoolconfig), pytoolconfig (rope dependency)
        # Removed: pyflakes, pycodestyle, mccabe, pylint, pydocstyle, pylama, autopep8 (replaced by ruff)
        # Removed: snowball_py (was only used by pydocstyle)
        # Removed: toml (not used; Ruff handles its own TOML parsing)
        # Removed: appdirs (not used anywhere)
        # Removed: astroid (not needed; was only for pylint)
        required_submodules = ['rope', 'tomli', 'pytoolconfig']
        for module in required_submodules:
            module_full_path = os.path.join(dir_submodule, module)
            if os.path.exists(module_full_path) and module_full_path not in sys.path:
                sys.path.insert(0, module_full_path)
