import _ast

from .mccabe import get_code_complexity
from .pep8 import BaseReport, StyleGuide
from .pyflakes import checker


__all__ = 'pep8', 'mccabe', 'pyflakes', 'pylint'


class PEP8Report(BaseReport):

    def __init__(self, *args, **kwargs):
        super(PEP8Report, self).__init__(*args, **kwargs)
        self.errors = []

    def init_file(self, filename, lines, expected, line_offset):
        super(PEP8Report, self).init_file(
            filename, lines, expected, line_offset)
        self.errors = []

    def error(self, line_number, offset, text, check):
        code = super(PEP8Report, self).error(
            line_number, offset, text, check)

        self.errors.append(dict(
            text=text,
            type=code,
            col=offset + 1,
            lnum=line_number,
        ))

    def get_file_results(self):
        return self.errors

P8Style = StyleGuide(reporter=PEP8Report)


def pep8(path, **meta):
    " PEP8 code checking. "

    return P8Style.input_file(path)


def mccabe(path, code=None, complexity=8, **meta):
    " MCCabe code checking. "

    return get_code_complexity(code, complexity, filename=path)


def pyflakes(path, code=None, **meta):
    " PyFlakes code checking. "

    errors = []
    tree = compile(code, path, "exec", _ast.PyCF_ONLY_AST)
    w = checker.Checker(tree, path)
    w.messages.sort(lambda a, b: cmp(a.lineno, b.lineno))
    for w in w.messages:
        errors.append(dict(
            lnum=w.lineno,
            text=w.message % w.message_args,
        ))
    return errors


def pylint(path, **meta):
    from .pylint.lint import Run
    from .pylint.reporters import BaseReporter

    from .pylint.logilab.astng.builder import MANAGER
    MANAGER.astng_cache.clear()

    class Reporter(BaseReporter):

        def __init__(self):
            self.errors = []
            BaseReporter.__init__(self)

        def _display(self, layout):
            pass

        def add_message(self, msg_id, location, msg):
            _, _, line, col = location[1:]
            self.errors.append(dict(
                lnum=line,
                col=col,
                text="%s %s" % (msg_id, msg),
                type=msg_id[0]
            ))

    attrs = meta.get('pylint', [])

    runner = Run(
        [path] + attrs, reporter=Reporter(), exit=False)
    return runner.linter.reporter.errors

# pymode:lint_ignore=W0231
