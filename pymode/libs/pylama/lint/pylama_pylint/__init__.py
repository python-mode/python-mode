""" Description. """

# Module information
# ==================


__version__ = '0.1.5'
__project__ = 'pylama_pylint'
__author__ = "horneds <horneds@gmail.com>"
__license__ = "BSD"

import os.path
import sys

if sys.version_info >= (3, 0, 0):
    raise ImportError("pylama_pylint doesnt support python3")

CURDIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, CURDIR)

from .main import Linter
assert Linter
