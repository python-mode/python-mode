""" Description. """

# Module information
# ==================


__version__ = '0.1.3'
__project__ = 'pylama_pylint'
__author__ = "horneds <horneds@gmail.com>"
__license__ = "BSD"

try:
    from .main import Linter
except ImportError:
    Linter = None
