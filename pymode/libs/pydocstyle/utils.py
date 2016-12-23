"""General shared utilities."""
import logging


__version__ = '1.1.1'
log = logging.getLogger(__name__)


def is_blank(string):
    """Return True iff the string contains only whitespaces."""
    return not string.strip()
