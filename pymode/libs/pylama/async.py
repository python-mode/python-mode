"""Support for checking code asynchronously."""

import logging
import threading

try:
    import Queue
except ImportError:
    import queue as Queue


try:
    import multiprocessing

    CPU_COUNT = multiprocessing.cpu_count()

except (ImportError, NotImplementedError):
    CPU_COUNT = 1

from .core import run


LOGGER = logging.getLogger('pylama')


class Worker(threading.Thread):
    """Get tasks from queue and run."""

    def __init__(self, path_queue, result_queue):
        """ Init worker. """
        threading.Thread.__init__(self)
        self.path_queue = path_queue
        self.result_queue = result_queue

    def run(self):
        """ Run tasks from queue. """
        while True:
            path, params = self.path_queue.get()
            errors = run(path, **params)
            self.result_queue.put(errors)
            self.path_queue.task_done()


def check_async(paths, options, rootdir=None):
    """Check given paths asynchronously.

    :return list: list of errors

    """
    LOGGER.info('Async code checking is enabled.')
    path_queue = Queue.Queue()
    result_queue = Queue.Queue()

    for num in range(CPU_COUNT):
        worker = Worker(path_queue, result_queue)
        worker.setDaemon(True)
        LOGGER.info('Start worker #%s', (num + 1))
        worker.start()

    for path in paths:
        path_queue.put((path, dict(options=options, rootdir=rootdir)))

    path_queue.join()

    errors = []
    while True:
        try:
            errors += result_queue.get(False)
        except Queue.Empty:
            break

    return errors


# pylama:ignore=W0212,D210,F0001
