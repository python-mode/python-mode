"""ropevim, a vim mode for using rope refactoring library"""
import os
import tempfile
import re

import ropemode.decorators
import ropemode.environment
import ropemode.interface

import vim


class VimUtils(ropemode.environment.Environment):

    def __init__(self, *args, **kwargs):
        super(VimUtils, self).__init__(*args, **kwargs)
        self.completeopt = vim.eval('&completeopt')
        self.preview = 'preview' in self.completeopt

    def ask(self, prompt, default=None, starting=None):
        if starting is None:
            starting = ''
        if default is not None:
            prompt = prompt + ('[%s] ' % default)
        result = call('input("%s", "%s")' % (prompt, starting))
        if default is not None and result == '':
            return default
        return result

    def ask_values(self, prompt, values, default=None,
                   starting=None, show_values=None):
        if show_values or (show_values is None and len(values) < 14):
            self._print_values(values)
        if default is not None:
            prompt = prompt + ('[%s] ' % default)
        starting = starting or ''
        _completer.values = values
        answer = call('input("%s", "%s", "customlist,RopeValueCompleter")' %
                      (prompt, starting))
        if answer is None:
            if 'cancel' in values:
                return 'cancel'
            return
        if default is not None and not answer:
            return default
        if answer.isdigit() and 0 <= int(answer) < len(values):
            return values[int(answer)]
        return answer

    def ask_directory(self, prompt, default=None, starting=None):
        return call('input("%s", ".", "dir")' % prompt)

    def _update_proposals(self, values):
        self.completeopt = vim.eval('&completeopt')
        self.preview = 'preview' in self.completeopt

        if not self.get('extended_complete'):
            return u','.join(u"'%s'" % self._completion_text(proposal)
                                    for proposal in values)

        return u','.join(self._extended_completion(proposal)
                                    for proposal in values)

    def _command(self, command, encode=False):
        if encode:
            command = command.encode(self._get_encoding())
        vim.command(command)

    def ask_completion(self, prompt, values, starting=None):
        if self.get('vim_completion') and 'i' in call('mode()'):
            proposals = self._update_proposals(values)
            col = int(call('col(".")'))
            if starting:
                col -= len(starting)
            self._command(u'call complete(%s, [%s])' % (col, proposals),
                    encode=True)
            return None

        return self.ask_values(prompt, values, starting=starting,
                               show_values=False)

    def message(self, message):
        echo(message)

    @staticmethod
    def _print_values(values):
        numbered = []
        for index, value in enumerate(values):
            numbered.append('%s. %s' % (index, str(value)))
        echo('\n'.join(numbered) + '\n')

    def yes_or_no(self, prompt):
        return self.ask_values(prompt, ['yes', 'no']) == 'yes'

    def y_or_n(self, prompt):
        return self.yes_or_no(prompt)

    def get(self, name):
        vimname = 'g:pymode_rope_%s' % name
        result = vim.eval(vimname)
        if isinstance(result, str) and result.isdigit():
            return int(result)
        return result

    def get_offset(self):
        result = self._position_to_offset(*self.cursor)
        return result

    @staticmethod
    def _get_encoding():
        return vim.eval('&encoding')

    def _encode_line(self, line):
        return line.encode(self._get_encoding())

    def _decode_line(self, line):
        return line.decode(self._get_encoding())

    def _position_to_offset(self, lineno, colno):
        result = min(colno, len(vim.current.buffer[lineno -1]) + 1)
        for line in vim.current.buffer[:lineno-1]:
            line = self._decode_line(line)
            result += len(line) + 1
        return result

    def get_text(self):
        return self._decode_line('\n'.join(vim.current.buffer)) + u'\n'

    def get_region(self):
        start = self._position_to_offset(*vim.current.buffer.mark('<'))
        end = self._position_to_offset(*vim.current.buffer.mark('>'))
        return start, end

    def _get_cursor(self):
        lineno, col = vim.current.window.cursor
        line = self._decode_line(vim.current.line[:col])
        col = len(line)
        return (lineno, col)

    def _set_cursor(self, cursor):
        lineno, col = cursor
        line = self._decode_line(vim.current.line)
        line = self._encode_line(line[:col])
        col = len(line)
        vim.current.window.cursor = (lineno, col)

    cursor = property(_get_cursor, _set_cursor)

    @staticmethod
    def get_cur_dir():
        return vim.eval('getcwd()')

    def filename(self):
        return vim.current.buffer.name

    def is_modified(self):
        return vim.eval('&modified')

    def goto_line(self, lineno):
        self.cursor = (lineno, 0)

    def insert_line(self, line, lineno):
        vim.current.buffer[lineno - 1:lineno - 1] = [line]

    def insert(self, text):
        lineno, colno = self.cursor
        line = vim.current.buffer[lineno - 1]
        vim.current.buffer[lineno - 1] = line[:colno] + text + line[colno:]
        self.cursor = (lineno, colno + len(text))

    def delete(self, start, end):
        lineno1, colno1 = self._offset_to_position(start - 1)
        lineno2, colno2 = self._offset_to_position(end - 1)
        lineno, colno = self.cursor
        if lineno1 == lineno2:
            line = vim.current.buffer[lineno1 - 1]
            vim.current.buffer[lineno1 - 1] = line[:colno1] + line[colno2:]
            if lineno == lineno1 and colno >= colno1:
                diff = colno2 - colno1
                self.cursor = (lineno, max(0, colno - diff))

    def _offset_to_position(self, offset):
        text = self.get_text()
        lineno = text.count('\n', 0, offset) + 1
        try:
            colno = offset - text.rindex('\n', 0, offset) - 1
        except ValueError:
            colno = offset
        return lineno, colno

    def filenames(self):
        result = []
        for b in vim.buffers:
            if b.name:
                result.append(b.name)
        return result

    def save_files(self, filenames):
        vim.command('wall')

    def reload_files(self, filenames, moves=None):
        if moves is None:
            moves = dict()
        initial = self.filename()
        for filename in filenames:
            self.find_file(moves.get(filename, filename), force=True)
        if initial:
            self.find_file(initial)

    def find_file(self, filename, readonly=False, other=False, force=False):
        if filename != self.filename() or force:
            if other:
                vim.command('new')
            filename = '\\ '.join(s.rstrip() for s in filename.split())
            vim.command('e %s' % filename)
            if readonly:
                vim.command('set nomodifiable')

    def create_progress(self, name):
        return VimProgress(name)

    def current_word(self):
        return vim.eval('expand("<cword>")')

    def push_mark(self):
        vim.command('mark `')

    def prefix_value(self, prefix):
        return prefix

    def show_occurrences(self, locations):
        self._quickfixdefs(locations)
        vim.command('cwindow')

    def _quickfixdefs(self, locations):
        filename = os.path.join(tempfile.gettempdir(), tempfile.mktemp())
        try:
            self._writedefs(locations, filename)
            vim.command('let old_errorfile = &errorfile')
            vim.command('let old_errorformat = &errorformat')
            vim.command('set errorformat=%f:%l:\ %m')
            vim.command('cfile ' + filename)
            vim.command('let &errorformat = old_errorformat')
            vim.command('let &errorfile = old_errorfile')
        finally:
            os.remove(filename)

    @staticmethod
    def _writedefs(locations, filename):
        tofile = open(filename, 'w')
        try:
            for location in locations:
                err = '%s:%d: - %s\n' % (location.filename,
                                         location.lineno, location.note)
                tofile.write(err)
        finally:
            tofile.close()

    def show_doc(self, docs, altview=False):
        if docs:
            cmd = 'call pymode#ShowStr("%s")' % str(docs.replace('"', '\\"'))
            print cmd
            vim.command(cmd)

    def preview_changes(self, diffs):
        echo(diffs)
        return self.y_or_n('Do the changes? ')

    def local_command(self, name, callback, key=None, prefix=False):
        self._add_command(name, callback, key, prefix,
                          prekey=self.get('local_prefix'))

    def global_command(self, name, callback, key=None, prefix=False):
        self._add_command(name, callback, key, prefix,
                          prekey=self.get('global_prefix'))

    def add_hook(self, name, callback, hook):
        mapping = {'before_save': 'FileWritePre,BufWritePre',
                   'after_save': 'FileWritePost,BufWritePost',
                   'exit': 'VimLeave'}
        self._add_function(name, callback)
        vim.command('autocmd %s *.py call %s()' %
                    (mapping[hook], _vim_name(name)))

    def _add_command(self, name, callback, key, prefix, prekey):
        self._add_function(name, callback, prefix)
        vim.command('command! -range %s call %s()' %
                    (_vim_name(name), _vim_name(name)))
        if key is not None:
            key = prekey + key.replace(' ', '')
            vim.command('map %s :call %s()<cr>' % (key, _vim_name(name)))

    @staticmethod
    def _add_function(name, callback, prefix=False):
        globals()[name] = callback
        arg = 'None' if prefix else ''
        vim.command('function! %s()\n' % _vim_name(name) +
                    'python ropevim.%s(%s)\n' % (name, arg) +
                    'endfunction\n')

    def _completion_data(self, proposal):
        return proposal

    _docstring_re = re.compile('^[\s\t\n]*([^\n]*)')

    def _extended_completion(self, proposal):
        # we are using extended complete and return dicts instead of strings.
        # `ci` means "completion item". see `:help complete-items`
        word, _, menu = map(lambda x: x.strip(), proposal.name.partition(':'))
        ci = dict(
                word = word,
                info = '',
                kind = ''.join(s if s not in 'aeyuo' else '' for s in proposal.type)[:3],
                menu = menu or '')

        if proposal.scope == 'parameter_keyword':
            default = proposal.get_default()
            ci["menu"] += '*' if default is None else '= %s' % default

        if self.preview and not ci['menu']:
            doc = proposal.get_doc()
            ci['info'] = self._docstring_re.match(doc).group(1) if doc else ''

        return self._conv(ci)

    def _conv(self, obj):
        if isinstance(obj, dict):
            return u'{' + u','.join([
                u"%s:%s" % (self._conv(key), self._conv(value))
                for key, value in obj.iteritems()]) + u'}'
        return u'"%s"' % str(obj).replace(u'"', u'\\"')


def _vim_name(name):
    tokens = name.split('_')
    newtokens = ['Rope'] + [token.title() for token in tokens]
    return ''.join(newtokens)


class VimProgress(object):

    def __init__(self, name):
        self.name = name
        self.last = 0
        status('%s ... ' % self.name)

    def update(self, percent):
        try:
            vim.eval('getchar(0)')
        except vim.error:
            raise KeyboardInterrupt('Task %s was interrupted!' % self.name)
        if percent > self.last + 4:
            status('%s ... %s%%%%' % (self.name, percent))
            self.last = percent

    def done(self):
        status('%s ... done' % self.name)


def echo(message):
    if isinstance(message, unicode):
        message = message.encode(vim.eval('&encoding'))
    print message

def status(message):
    if isinstance(message, unicode):
        message = message.encode(vim.eval('&encoding'))
    vim.command('redraw | echon "%s"' % message)

def call(command):
    return vim.eval(command)

class _ValueCompleter(object):

    def __init__(self):
        self.values = []
        vim.command('python import vim')
        vim.command('function! RopeValueCompleter(A, L, P)\n'
                    'python args = [vim.eval("a:" + p) for p in "ALP"]\n'
                    'python ropevim._completer(*args)\n'
                    'return s:completions\n'
                    'endfunction\n')

    def __call__(self, arg_lead, cmd_line, cursor_pos):
        # don't know if self.values can be empty but better safe then sorry
        if self.values:
            if not isinstance(self.values[0], basestring):
                result = [proposal.name for proposal in self.values \
                          if proposal.name.startswith(arg_lead)]
            else:
                result = [proposal for proposal in self.values \
                          if proposal.startswith(arg_lead)]
            vim.command('let s:completions = %s' % result)



ropemode.decorators.logger.message = echo
ropemode.decorators.logger.only_short = True

_completer = _ValueCompleter()

_env = VimUtils()
_interface = ropemode.interface.RopeMode(env=_env)
