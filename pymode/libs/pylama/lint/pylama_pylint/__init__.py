""" Description. """

# Module information
# ==================


__version__ = '0.1.3'
__project__ = 'pylama_pylint'
__author__ = "horneds <horneds@gmail.com>"
__license__ = "BSD"

import os.path
import sys

CURDIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, CURDIR)

from .main import Linter
assert Linter

