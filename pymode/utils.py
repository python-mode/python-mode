""" Pymode utils. """
import sys

import json

import vim # noqa


PY2 = sys.version_info[0] == 2


def args_from_vim(func):
    """ Proxy arguments from Vim function to Python function.

    :return func: A wrapper

    """
    def __wrapper():
        args = vim.eval('a:000')
        return func(*args)
    return __wrapper


def pymode_message(content):
    """ Show message. """

    vim.command('call pymode#wide_message("%s")' % str(content))


def pymode_confirm(yes=True, msg='Do the changes:'):
    """ Confirmation.

    :return bool:

    """
    default = 'yes' if yes else 'no'
    action = pymode_input(msg, default)
    return action and 'yes'.startswith(action)


def pymode_inputlist(msg, opts):
    """ Get user choice.

    :return str: A choosen option

    """
    choices = ['[Pymode] %s' % msg]
    choices += ["%s. %s" % (num, opt) for num, opt in enumerate(opts, 1)]
    try:
        input_str = int(vim.eval('inputlist(%s)' % json.dumps(choices)))
    except (KeyboardInterrupt, ValueError):
        input_str = 0

    if not input_str:
        pymode_message('Cancelled!')
        return False

    try:
        return opts[input_str - 1]
    except (IndexError, ValueError):
        pymode_error('Invalid option: %s' % input_str)
        return pymode_inputlist(msg, opts)


def pymode_input(umsg, udefault='', opts=None):
    """ Get user input.

    :return str: A user input

    """
    msg = '[Pymode] %s ' % umsg
    default = udefault

    if default != '':
        msg += '[%s] ' % default

    try:
        vim.command('echohl Debug')
        input_str = vim.eval('input("%s> ")' % msg)
        vim.command('echohl none')
    except KeyboardInterrupt:
        input_str = ''

    return input_str or default


def pymode_error(content):
    """ Show error. """

    vim.command('call pymode#error("%s")' % str(content))


def with_metaclass(meta, *bases):
    """ Metaclass support.

    :return class:

    """

    class metaclass(meta):

        __call__ = type.__call__
        __init__ = type.__init__

        def __new__(cls, name, this_bases, d):
            if this_bases is None:
                return type.__new__(cls, name, (), d)
            return meta(name, bases, d)

    return metaclass('temporary_class', None, {})


def catch_and_print_exceptions(func):
    """ Catch any exception.

    :return func:

    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (Exception, vim.error) as e: # noqa
            pymode_error(e)
            return None
    return wrapper
