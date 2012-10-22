import traceback

from rope.base import exceptions


class Logger(object):

    message = None
    only_short = False

    def __call__(self, message, short=None):
        if short is None or not self.only_short:
            self._show(message)
        if short is not None:
            self._show(short)

    def _show(self, message):
        if self.message is None:
            print message
        else:
            self.message(message)

logger = Logger()


def lisphook(func):
    def newfunc(*args, **kwds):
        try:
            func(*args, **kwds)
        except Exception, e:
            trace = str(traceback.format_exc())
            short = 'Ignored an exception in ropemode hook: %s' % \
                    _exception_message(e)
            logger(trace, short)
    newfunc.lisp = None
    newfunc.__name__ = func.__name__
    newfunc.__doc__ = func.__doc__
    return newfunc


def lispfunction(func):
    func.lisp = None
    return func


input_exceptions = (exceptions.RefactoringError,
                    exceptions.ModuleSyntaxError,
                    exceptions.BadIdentifierError)

def _exception_handler(func):
    def newfunc(*args, **kwds):
        try:
            return func(*args, **kwds)
        except exceptions.RopeError, e:
            short = None
            if isinstance(e, input_exceptions):
                short = _exception_message(e)
            logger(str(traceback.format_exc()), short)
    newfunc.__name__ = func.__name__
    newfunc.__doc__ = func.__doc__
    return newfunc

def _exception_message(e):
    return '%s: %s' % (e.__class__.__name__, str(e))

def rope_hook(hook):
    def decorator(func):
        func = lisphook(func)
        func.name = func.__name__
        func.kind = 'hook'
        func.hook = hook
        return func
    return decorator


def local_command(key=None, prefix=False, shortcut=None, name=None):
    def decorator(func, name=name):
        func = _exception_handler(func)
        func.kind = 'local'
        func.prefix = prefix
        func.local_key = key
        func.shortcut_key = shortcut
        if name is None:
            name = func.__name__
        func.name = name
        return func
    return decorator


def global_command(key=None, prefix=False):
    def decorator(func):
        func = _exception_handler(func)
        func.kind = 'global'
        func.prefix = prefix
        func.global_key = key
        func.name = func.__name__
        return func
    return decorator
