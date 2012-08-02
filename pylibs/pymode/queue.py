import threading
from .interface import show_message
import time


class Task(threading.Thread):

    def __init__(self, buffer, callback=None, title=None, *args, **kwargs):
        self.buffer = buffer
        self._stop = threading.Event()
        self.result = None
        self.callback = callback
        self.done = 0
        self.finished = False
        self.title = title
        threading.Thread.__init__(self, *args, **kwargs)

    def run(self):
        " Run tasks. "
        self._Thread__target(task=self, *self._Thread__args, **self._Thread__kwargs)

        # Wait for result parsing
        while not self.stopped():
            time.sleep(.2)

    def stop(self):
        " Stop task. "
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()


def stop_queue():
    " Stop all tasks. "
    for thread in threading.enumerate():
        if isinstance(thread, Task):
            thread.stop()
            show_message('%s stopped.' % thread.title)


def add_task(target, callback=None, buffer=None, title=None, *args, **kwargs):
    " Add all tasks. "

    task = Task(buffer, title=title, target=target, callback=callback, args=args, kwargs=kwargs)
    task.daemon = True
    task.start()

    show_message('%s started.' % task.title)


def check_task():
    " Check tasks for result. "
    for thread in threading.enumerate():
        if isinstance(thread, Task):
            if thread.finished:
                thread.stop()
                thread.callback(thread.result)
            else:
                show_message('%s %s%%' % (thread.title, thread.done))
