import os
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

    add_task(
        run_checkers, checkers=checkers, ignore=ignore, title='Code checking',
        callback=parse_result, buffer=buffer, select=select
    )


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

    extra_kwargs = {}

    ignore = set(
        filter(
            lambda i: i, get_option('lint_ignore').split(',') +
                         get_var('lint_ignore').split(',')
        )
    )
    open('/tmp/foo.txt', 'w').write(','.join(['{0}'.format(i) for i in ignore]) + '\n')

    select = set(
        filter(
            lambda s: s, get_option('lint_select').split(',') +
                         get_var('lint_select').split(',')
        )
    )

    lint_config = get_var('lint_config')
    if lint_config:
        lint_config = os.path.abspath(os.path.expanduser(lint_config))

    if os.path.exists(lint_config):
        extra_kwargs['config_file'] = lint_config
        if 'pep8' not in lint_config:
            # This is probably a pylintrc file, let's get some options from it
            from ConfigParser import RawConfigParser
            parser = RawConfigParser()
            parser.read(lint_config)
            if parser.has_section('FORMAT') and parser.has_option('FORMAT', 'max-line-length'):
                extra_kwargs['max_line_length'] = int(parser.get('FORMAT', 'max-line-length'))
            if parser.has_section('MESSAGES CONTROL') and parser.has_option('MESSAGES CONTROL', 'disable'):
                for code in [i.strip() for i in parser.get('MESSAGES CONTROL', 'disable').split(',')]:
                    ignore.add(code)
            if parser.has_section('MESSAGES CONTROL') and parser.has_option('MESSAGES CONTROL', 'enable'):
                for code in [i.strip() for i in parser.get('MESSAGES CONTROL', 'enable').split(',')]:
                    select.add(code)

    if ignore:
        extra_kwargs['ignore'] = list(ignore)
    if select:
        extra_kwargs['select'] = list(select)

    PEP8['style'] = p8.StyleGuide(reporter=_PEP8Report, **extra_kwargs)


def _ignore_error(e, select, ignore):
    for s in select:
        if e['text'].startswith(s):
            return True
    for i in ignore:
        if e['text'].startswith(i):
            return False
    return True
