""" Code runnning support. """

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

import json
import sys
import vim # noqa

from .utils import pymode_error


VIM_INPUT = lambda s: vim.eval('input("%s")' % s)


def run_code():
    """ Run python code in current buffer. """

    errors = []
    line1, line2 = vim.eval('a:line1'), vim.eval('a:line2')
    lines = __prepare_lines(line1, line2)

    context = dict(__name__='__main__', input=VIM_INPUT, raw_input=VIM_INPUT)

    sys.stdout, stdout_ = StringIO(), sys.stdout
    sys.stderr, stderr_ = StringIO(), sys.stderr

    try:
        code = compile(
            '\n'.join(lines) + '\n', vim.current.buffer.name, 'exec')
        exec(code, context) # noqa

    except SystemExit as e:
        if e.code:
            # A non-false code indicates abnormal termination.
            # A false code will be treated as a
            # successful run, and the error will be hidden from Vim
            pymode_error("Script exited with code %s" % e.code)
            vim.command('return')

    except Exception:
        import traceback
        err = traceback.format_exc()

    else:
        err = sys.stderr.getvalue()

    output = sys.stdout.getvalue().strip()
    sys.stdout, sys.stderr = stdout_, stderr_

    try:
        output = output.decode('utf-8').encode(vim.eval('&enc'))
    except AttributeError:
        pass

    errors += [er for er in err.splitlines() if er and "<string>" not in er]

    vim.command('let l:traceback = %s' % json.dumps(errors[2:]))
    vim.command('let l:output = %s' % json.dumps(
        [s for s in output.split('\n') if s]))


def __prepare_lines(line1, line2):

    lines = [l.rstrip() for l in vim.current.buffer[int(line1) - 1:int(line2)]]

    indent = 0
    for line in lines:
        if line:
            indent = len(line) - len(line.lstrip())
            break

    return [l[indent:] for l in lines]
