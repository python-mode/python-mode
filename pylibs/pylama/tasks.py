""" Async code checking.
"""
import logging
import threading
from os import path as op
try:
    import Queue
except ImportError:
    import queue as Queue

from .core import run


try:
    import multiprocessing

    CPU_COUNT = multiprocessing.cpu_count()

except (ImportError, NotImplementedError):
    CPU_COUNT = 1

LOGGER = logging.getLogger('pylama')


class Worker(threading.Thread):

    """ Get tasks from queue and run. """

    def __init__(self, path_queue, result_queue):
        threading.Thread.__init__(self)
        self.path_queue = path_queue
        self.result_queue = result_queue

    def run(self):
        """ Run tasks from queue. """
        while True:
            path, params = self.path_queue.get()
            errors = check_path(path, **params)
            self.result_queue.put(errors)
            self.path_queue.task_done()


def async_check_files(paths, async=False, linters=None, **params):
    """ Check paths.

    :return list: list of errors

    """

    errors = []

    # Disable async if pylint enabled
    async = async and not 'pylint' in linters
    params['linters'] = linters

    if not async:
        for path in paths:
            errors += check_path(path, **params)
        return errors

    LOGGER.info('Async code checking is enabled.')
    path_queue = Queue.Queue()
    result_queue = Queue.Queue()

    for _ in range(CPU_COUNT):
        worker = Worker(path_queue, result_queue)
        worker.setDaemon(True)
        worker.start()

    for path in paths:
        path_queue.put((path, params))

    path_queue.join()

    while True:
        try:
            errors += result_queue.get(False)
        except Queue.Empty:
            break

    return errors


def check_path(path, rootpath='.', ignore=None, select=None, linters=None,
               complexity=None, params=None):
    """ Check path.

    :return list: list of errors

    """

    LOGGER.info("Parse file: %s", path)
    params = params or dict()
    config = dict()

    for mask in params:
        if mask.match(path):
            config.update(params[mask])

    errors = []
    for error in run(
        path, ignore=ignore, select=select, linters=linters,
            complexity=complexity, config=config):
        try:
            error['rel'] = op.relpath(error['filename'], rootpath)
            error['col'] = error.get('col', 1)
            errors.append(error)
        except KeyError:
            continue
    return errors
