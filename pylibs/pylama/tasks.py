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


def async_check_files(paths, options, rootpath=None):
    """ Check paths.

    :return list: list of errors

    """

    errors = []

    # Disable async if pylint enabled
    async = options.async and not 'pylint' in options.linters

    if not async:
        for path in paths:
            errors += check_path(path, options=options, rootpath=rootpath)
        return errors

    LOGGER.info('Async code checking is enabled.')
    path_queue = Queue.Queue()
    result_queue = Queue.Queue()

    for _ in range(CPU_COUNT):
        worker = Worker(path_queue, result_queue)
        worker.setDaemon(True)
        worker.start()

    for path in paths:
        path_queue.put((path, dict(options=options, rootpath=rootpath)))

    path_queue.join()

    while True:
        try:
            errors += result_queue.get(False)
        except Queue.Empty:
            break

    return errors


def check_path(path, options=None, rootpath=None, **meta):
    """ Check path.

    :return list: list of errors

    """

    LOGGER.info("Parse file: %s", path)
    config = dict()
    if rootpath is None:
        rootpath = '.'

    for mask in options.file_params:
        if mask.match(path):
            config.update(options.file_params[mask])

    errors = []
    for error in run(
        path, ignore=options.ignore, select=options.select,
        linters=options.linters, complexity=options.complexity,
            config=config, **meta):
        try:
            error['rel'] = op.relpath(error['filename'], rootpath)
            error['col'] = error.get('col', 1)
            errors.append(error)
        except KeyError:
            continue
    return errors
