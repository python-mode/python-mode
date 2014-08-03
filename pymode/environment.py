""" Define interfaces. """

from __future__ import print_function

import vim
import json
import time
import os.path

from ._compat import PY2


class VimPymodeEnviroment(object):

    """ Vim User interface. """

    prefix = '[Pymode]'

    def __init__(self):
        """ Init VIM environment. """
        self.current = vim.current
        self.options = dict(encoding=vim.eval('&enc'))
        self.options['debug'] = self.var('g:pymode_debug', True)

    @property
    def curdir(self):
        """ Return current working directory. """
        return self.var('getcwd()')

    @property
    def curbuf(self):
        """ Return current buffer. """
        return self.current.buffer

    @property
    def cursor(self):
        """ Return current window position.

        :return tuple: (row, col)

        """
        return self.current.window.cursor

    @property
    def source(self):
        """ Return source of current buffer. """
        return "\n".join(self.lines)

    @property
    def lines(self):
        """ Iterate by lines in current file.

        :return list:

        """
        if not PY2:
            return self.curbuf

        return [l.decode(self.options.get('encoding')) for l in self.curbuf]

    @staticmethod
    def var(name, to_bool=False, silence=False):
        """ Get vim variable.

        :return vimobj:

        """
        try:
            value = vim.eval(name)
        except vim.error:
            if silence:
                return None
            raise

        if to_bool:
            try:
                value = bool(int(value))
            except ValueError:
                value = value
        return value

    @staticmethod
    def message(msg, history=False):
        """ Show message to user.

        :return: :None

        """
        if history:
            return vim.command('echom "%s"' % str(msg))

        return vim.command('call pymode#wide_message("%s")' % str(msg))

    def user_input(self, msg, default=''):
        """ Return user input or default.

        :return str:

        """
        msg = '%s %s ' % (self.prefix, msg)

        if default != '':
            msg += '[%s] ' % default

        try:
            vim.command('echohl Debug')
            input_str = vim.eval('input("%s> ")' % msg)
            vim.command('echohl none')
        except KeyboardInterrupt:
            input_str = ''

        return input_str or default

    def user_confirm(self, msg, yes=False):
        """ Get user confirmation.

        :return bool:

        """
        default = 'yes' if yes else 'no'
        action = self.user_input(msg, default)
        return action and 'yes'.startswith(action)

    def user_input_choices(self, msg, *options):
        """ Get one of many options.

        :return str: A choosen option

        """
        choices = ['%s %s' % (self.prefix, msg)]
        choices += [
            "%s. %s" % (num, opt) for num, opt in enumerate(options, 1)]
        try:
            input_str = int(
                vim.eval('inputlist(%s)' % self.prepare_value(choices)))
        except (KeyboardInterrupt, ValueError):
            input_str = 0

        if not input_str:
            self.message('Cancelled!')
            return False

        try:
            return options[input_str - 1]
        except (IndexError, ValueError):
            self.error('Invalid option: %s' % input_str)
            return self.user_input_choices(msg, *options)

    @staticmethod
    def error(msg):
        """ Show error to user. """
        vim.command('call pymode#error("%s")' % str(msg))

    def debug(self, msg, *args):
        """ Print debug information. """
        if self.options.get('debug'):
            print("%s %s [%s]" % (
                int(time.time()), msg, ', '.join([str(a) for a in args])))

    def stop(self, value=None):
        """ Break Vim function. """
        cmd = 'return'
        if value is not None:
            cmd += ' ' + self.prepare_value(value)
        vim.command(cmd)

    def catch_exceptions(self, func):
        """ Decorator. Make execution more silence.

        :return func:

        """
        def _wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except (Exception, vim.error) as e: # noqa
                if self.options.get('debug'):
                    raise
                self.error(e)
                return None
        return _wrapper

    def run(self, name, *args):
        """ Run vim function. """
        vim.command('call %s(%s)' % (name, ", ".join([
            self.prepare_value(a) for a in args
        ])))

    def let(self, name, value):
        """ Set variable. """
        cmd = 'let %s = %s' % (name, self.prepare_value(value))
        self.debug(cmd)
        vim.command(cmd)

    def prepare_value(self, value, dumps=True):
        """ Decode bstr to vim encoding.

        :return unicode string:

        """
        if dumps:
            value = json.dumps(value)

        if PY2:
            value = value.decode('utf-8').encode(self.options.get('encoding'))

        return value

    def get_offset_params(self, cursor=None, base=""):
        """ Calculate current offset.

        :return tuple: (source, offset)

        """
        row, col = cursor or env.cursor
        source = ""
        offset = 0
        for i, line in enumerate(self.lines, 1):
            if i == row:
                source += line[:col] + base
                offset = len(source)
                source += line[col:]
            else:
                source += line
            source += '\n'
        env.debug('Get offset', base or None, row, col, offset)
        return source, offset

    @staticmethod
    def goto_line(line):
        """ Go to line. """
        vim.command('normal %sggzz' % line)

    def goto_file(self, path, cmd='e', force=False):
        """ Function description. """
        if force or os.path.abspath(path) != self.curbuf.name:
            self.debug('read', path)
            if ' ' in path and os.name == 'posix':
                path = path.replace(' ', '\\ ')
            vim.command("%s %s" % (cmd, path))

    @staticmethod
    def goto_buffer(bufnr):
        """ Open buffer. """
        if str(bufnr) != '-1':
            vim.command('buffer %s' % bufnr)


env = VimPymodeEnviroment()
