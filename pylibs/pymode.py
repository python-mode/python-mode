import StringIO
import locale

import vim


locale.setlocale(locale.LC_CTYPE, "C")


def check_file():
    filename = vim.current.buffer.name
    checkers = vim.eval('g:pymode_lint_checker').split(',')
    ignore = vim.eval("g:pymode_lint_ignore")
    ignore = ignore and ignore.split(',') or []
    select = vim.eval("g:pymode_lint_select")
    select = select and select.split(',') or []
    errors = []

    for c in checkers:
        checker = globals().get(c)
        if checker:
            try:
                errors += checker(filename)
            except SyntaxError, e:
                errors.append(dict(
                    lnum=e.lineno,
                    col=e.offset,
                    text=e.args[0]
                ))
                break
            except Exception, e:
                print e

    for e in errors:
        e.update(
            col=e.get('col') or '',
            text=e.get('text', '').replace("'", "\"").split('\n')[0],
            filename=filename,
            bufnr=vim.current.buffer.number,
        )

    errors = filter(lambda e: _ignore_error(e, select, ignore), errors)
    errors = sorted(errors, key=lambda x: x['lnum'])

    vim.command(('let b:qf_list = %s' % repr(errors)).replace('\': u', '\': '))


def mccabe(filename):
    import mccabe as mc

    complexity = int(vim.eval("g:pymode_lint_mccabe_complexity"))
    return mc.get_module_complexity(filename, min=complexity)


def pep8(filename):
    PEP8 or _init_pep8()
    checker = PEP8['module'].Checker(filename)
    checker.check_all()
    return checker.errors


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

    class _PEP8Options(object):
        # Default options taken from pep8.process_options()
        verbose = False
        quiet = False
        repeat = True
        exclude = [exc.rstrip('/') for exc in p8.DEFAULT_EXCLUDE.split(',')]
        select = []
        ignore = p8.DEFAULT_IGNORE.split(',')  # or []?
        show_source = False
        show_pep8 = False
        statistics = False
        count = False
        benchmark = False
        testsuite = ''
        max_line_length = p8.MAX_LINE_LENGTH
        filename = ['*.py']
        doctest = False

        logical_checks = physical_checks = None
        messages = counters = None

    # default p8 setup
    p8.options = _PEP8Options()
    p8.options.physical_checks = p8.find_checks('physical_line')
    p8.options.logical_checks = p8.find_checks('logical_line')
    p8.options.counters = dict.fromkeys(p8.BENCHMARK_KEYS, 0)
    p8.options.messages = {}
    p8.args = []

    PEP8['init'] = True
    PEP8['module'] = p8


def _ignore_error(e, select, ignore):
    for s in select:
        if e['text'].startswith(s):
            return True
    for i in ignore:
        if e['text'].startswith(i):
            return False
    return True
