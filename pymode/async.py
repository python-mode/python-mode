""" Python-mode async support. """
try:
    from Queue import Queue
except ImportError:
    from queue import Queue # noqa


RESULTS = Queue()
