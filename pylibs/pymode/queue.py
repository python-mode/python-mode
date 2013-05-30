from __future__ import absolute_import

import threading
from Queue import Queue, Empty

from .interface import show_message


MAX_LIFE = 60
CHECK_INTERVAL = .2
RESULTS = Queue()
TEST = 1


class Task(threading.Thread):

    def __init__(self, *args, **kwargs):
        threading.Thread.__init__(self, *args, **kwargs)
        self.stop = threading.Event()

    def run(self):
        """ Run the task.
        """
        try:
            args, kwargs = self._Thread__args, self._Thread__kwargs
            checking = self._Thread__target(*args, **kwargs)
            if not self.stop.isSet():
                RESULTS.put((checking, args, kwargs))

        except Exception as e:
            if not self.stop.isSet():
                RESULTS.put(e)


def add_task(target, title=None, *args, **kwargs):
    " Add all tasks. "

    # Only one task at time
    for thread in threading.enumerate():
        if isinstance(thread, Task):
            return True

    task = Task(target=target, args=args, kwargs=kwargs)
    task.daemon = True
    task.start()

    show_message('{0} started.'.format(title))


def stop_queue(message=True):
    """ Stop all tasks.
    """
    with RESULTS.mutex:
        RESULTS.queue.clear()

    for thread in threading.enumerate():
        if isinstance(thread, Task):
            thread.stop.set()
            if message:
                show_message("Task stopped.")


def check_task():
    """ Checking running tasks.
    """
    try:
        result = RESULTS.get(False)
        assert isinstance(result, tuple)
    except Empty:
        return False
    except AssertionError:
        return False
    result, _, kwargs = result
    callback = kwargs.pop('callback')
    callback(result, **kwargs)


# lint_ignore=W0703
