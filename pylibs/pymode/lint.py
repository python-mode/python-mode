import StringIO
import locale

from .interface import get_option, get_var, get_current_buffer, command
from .queue import add_task


locale.setlocale(locale.LC_CTYPE, "C")


def check_file():
    checkers = get_option('lint_checker').split(',')

    ignore = set(filter(lambda i: i, get_option('lint_ignore').split(',') +
                 get_var('lint_ignore').split(',')))

    select = set(filter(lambda s: s, get_option('lint_select').split(',') +
                 get_var('lint_select').split(',')))

    buffer = get_current_buffer()

    add_task(run_checkers, checkers=checkers, ignore=ignore, title='Code checking', callback=parse_result, buffer=buffer, select=select)


def run_checkers(task=None, checkers=None, ignore=None, buffer=None, select=None):

    buffer = (task and task.buffer) or buffer
    filename = buffer.name
    result = []
    part = 100 / len(checkers)

    for c in checkers:

        checker = globals().get(c)
        if not checker:
            continue

        try:
            for e in checker(filename):
                e.update(
                    col=e.get('col') or 0,
                    text="%s [%s]" % (e.get('text', '')
                                      .strip().replace("'", "\"").split('\n')[0], c),
                    filename=filename,
                    bufnr=buffer.number,
                )
                result.append(e)

        except SyntaxError, e:
            result.append(dict(
                lnum=e.lineno,
                col=e.offset or 0,
                text=e.args[0],
                bufnr=buffer.number,
            ))
            break

        except Exception, e:
            assert True

        if task:
            task.done += part

    result = filter(lambda e: _ignore_error(e, select, ignore), result)
    result = sorted(result, key=lambda x: x['lnum'])

    if task:
        task.result = result
        task.finished = True
        task.done = 100


def parse_result(result):
    command(('let g:qf_list = %s' % repr(result)).replace('\': u', '\': '))
    command('call pymode#lint#Parse()')


def mccabe(filename):
    from pylibs.mccabe import get_code_complexity

    complexity = int(get_option('lint_mccabe_complexity'))
    return mc.get_module_complexity(filename, min=complexity)


def pep8(filename):
    PEP8 or _init_pep8()
    style = PEP8['style']
    return style.input_file(filename)


def pylint(filename):
    from pylibs.logilab.astng.builder import MANAGER

    PYLINT or _init_pylint()
    linter = PYLINT['lint']

    MANAGER.astng_cache.clear()
    linter.reporter.out = StringIO.StringIO()
    linter.check(filename)
    errors, linter.reporter.errors = linter.reporter.errors, []
    return errors


def pyflakes(filename):
    from pylibs.pyflakes import checker
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

    from pylibs.pylint import lint, checkers, reporters
    import re

    class VimReporter(reporters.BaseReporter):

        def __init__(self):
            reporters.BaseReporter.__init__(self)
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
    PYLINT['re'] = re.compile(
        '^(?:.:)?[^:]+:(\d+): \[([EWRCI]+)[^\]]*\] (.*)$')

    checkers.initialize(PYLINT['lint'])
    PYLINT['lint'].load_file_configuration(get_var('lint_config'))
    PYLINT['lint'].set_option("output-format", "parseable")
    PYLINT['lint'].set_option("include-ids", 1)
    PYLINT['lint'].set_option("reports", 0)
    PYLINT['lint'].reporter = VimReporter()


PEP8 = dict()


def _init_pep8():

    from pylibs import pep8 as p8

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
