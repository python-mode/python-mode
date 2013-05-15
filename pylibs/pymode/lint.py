import locale

from pylama.main import run

from .interface import get_option, get_var, get_current_buffer, command
from .queue import add_task


try:
    locale.setlocale(locale.LC_CTYPE, "C")
except AttributeError:
    pass


def check_file():
    checkers = get_option('lint_checker').split(',')

    ignore = set([
        i for i in (
            get_option('lint_ignore').split(',') +
            get_var('lint_ignore').split(','))
        if i
    ])
    select = set([
        s for s in (
            get_option('lint_select').split(',') +
            get_var('lint_select').split(','))
        if s
    ])

    buf = get_current_buffer()
    complexity = int(get_option('lint_mccabe_complexity') or 0)

    add_task(
        run_checkers,
        callback=parse_result,
        title='Code checking',

        checkers=checkers,
        ignore=ignore,
        buf=buf,
        select=select,
        complexity=complexity)


def run_checkers(checkers=None, ignore=None, buf=None, select=None,
                 complexity=None, callback=None):

    filename = buf.name
    result = []

    pylint_options = '--rcfile={0} -r n'.format(get_var('lint_config')).split()

    return run(filename, ignore=ignore, select=select, linters=checkers,
                 pylint=pylint_options, complexity=complexity)


def parse_result(result, buf=None, **kwargs):
    command(('let g:qf_list = {0}'.format(repr(result)).replace(
        '\': u', '\': ')))
    command('call pymode#lint#Parse({0})'.format(buf.number))

# pymode:lint_ignore=W0622
