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

    pylint_options = '--rcfile={0} -r n'.format(get_var('lint_config')).split()

    result = run(filename, ignore=ignore, select=select, linters=checkers, pylint=pylint_options)

    if task:
        task.result = result
        task.finished = True
        task.done = 100


def parse_result(result):
    command(('let g:qf_list = %s' % repr(result)).replace('\': u', '\': '))
    command('call pymode#lint#Parse()')
