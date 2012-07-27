import StringIO
import locale
import threading

import vim


locale.setlocale(locale.LC_CTYPE, "C")


def check_file():
    checkers = vim.eval("pymode#Option('lint_checker')").split(',')

    ignore = set(filter(lambda i: i, vim.eval("pymode#Option('lint_ignore')").split(',') +
                 vim.eval("g:pymode_lint_ignore").split(',')))

    select = set(filter(lambda s: s, vim.eval("pymode#Option('lint_select')").split(',') +
                 vim.eval("g:pymode_lint_select").split(',')))

    # Stop current threads
    stop_checkers()

    # Create new thread
    thread = Checker(vim.current.buffer, select, ignore, checkers)
    thread.start()


def stop_checkers():
    for thread in threading.enumerate():
        if isinstance(thread, Checker):
            thread.stop()


class Checker(threading.Thread):
    def __init__(self, buffer, select, ignore, checkers):
        self.buffer = buffer.number
        self.filename = buffer.name
        self.select = select
        self.ignore = ignore
        self.checkers = checkers
        self._stop = threading.Event()
        super(Checker, self).__init__()

    def run(self):
        " Run code checking. "

        errors = []

        for c in self.checkers:

            if self.stopped():
                return True

            checker = globals().get(c)
            if checker:
                try:
                    for e in checker(self.filename):
                        e.update(
                            col=e.get('col') or '',
                            text="%s [%s]" % (e.get('text', '').strip().replace("'", "\"").split('\n')[0], c),
                            filename=self.filename,
                            bufnr=self.buffer,
                        )
                        errors.append(e)

                except SyntaxError, e:
                    errors.append(dict(
                        lnum=e.lineno,
                        col=e.offset,
                        text=e.args[0]
                    ))
                    break
                except Exception, e:
                    print e

        if self.stopped():
            return True

        errors = filter(lambda e: _ignore_error(e, self.select, self.ignore), errors)
        errors = sorted(errors, key=lambda x: x['lnum'])

        vim.command(('let g:qf_list = %s' % repr(errors)).replace('\': u', '\': '))
        vim.command('call pymode#lint#Parse()')

    def stop(self):
        " Stop code checking. "
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()


def mccabe(filename):
    import mccabe as mc

    complexity = int(vim.eval("pymode#Option('lint_mccabe_complexity')"))
    return mc.get_module_complexity(filename, min=complexity)


def pep8(filename):
    PEP8 or _init_pep8()
    style = PEP8['style']
    return style.input_file(filename)


def pylint(filename):
    from logilab.astng.builder import MANAGER

    PYLINT or _init_pylint()
    linter = PYLINT['lint']

    MANAGER.astng_cache.clear()
    linter.reporter.out = StringIO.StringIO()
    linter.check(filename)
    errors, linter.reporter.errors = linter.reporter.errors, []
    return errors


def pyflakes(filename):
    from pyflakes import checker
    import _ast

    codeString = file(filename, 'U').read() + '\n'
    errors = []
    tree = compile(codeString, filename, "exec", _ast.PyCF_ONLY_AST)
    w = checker.Checker(tree, filename)
    w.messages.sort(lambda a, b: cmp(a.lineno, b.lineno))
    for w in w.messages:
        errors.append(dict(
            lnum=w.lineno,
            col=w.col,
            text=w.message % w.message_args,
            type='E'
        ))
    return errors


PYLINT = dict()


def _init_pylint():

    from pylint import lint, checkers
    import re

    class VimReporter(object):
        def __init__(self):
            self.errors = []

        def add_message(self, msg_id, location, msg):
            _, _, line, col = location[1:]
            self.errors.append(dict(
                lnum=line,
                col=col,
                text="%s %s" % (msg_id, msg),
                type=msg_id[0]
            ))

    PYLINT['lint'] = lint.PyLinter()
    PYLINT['re'] = re.compile('^(?:.:)?[^:]+:(\d+): \[([EWRCI]+)[^\]]*\] (.*)$')

    checkers.initialize(PYLINT['lint'])
    PYLINT['lint'].load_file_configuration(vim.eval("g:pymode_lint_config"))
    PYLINT['lint'].set_option("output-format", "parseable")
    PYLINT['lint'].set_option("include-ids", 1)
    PYLINT['lint'].set_option("reports", 0)
    PYLINT['lint'].reporter = VimReporter()


PEP8 = dict()


def _init_pep8():

    import pep8 as p8

    class _PEP8Report(p8.BaseReport):

        def init_file(self, filename, lines, expected, line_offset):
            super(_PEP8Report, self).init_file(
                filename, lines, expected, line_offset)
            self.errors = []

        def error(self, line_number, offset, text, check):
            code = super(_PEP8Report, self).error(
                line_number, offset, text, check)
            self.errors.append(dict(
                text=text,
                type=code,
                col=offset + 1,
                lnum=line_number,
            ))

        def get_file_results(self):
            return self.errors

    PEP8['style'] = p8.StyleGuide(reporter=_PEP8Report)


def _ignore_error(e, select, ignore):
    for s in select:
        if e['text'].startswith(s):
            return True
    for i in ignore:
        if e['text'].startswith(i):
            return False
    return True
