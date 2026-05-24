""" Code runnning support. """
import os
import subprocess
import sys
import tempfile
from io import StringIO
from re import compile as re

from .environment import env


encoding = re(r'#.*coding[:=]\s*([-\w.]+)')


def run_code():
    """ Run python code in current buffer.

    :returns: None

    """
    errors, err = [], ''
    line1, line2 = env.var('a:line1'), env.var('a:line2')
    lines = __prepare_lines(line1, line2)
    if encoding.match(lines[0]):
        lines.pop(0)
        if encoding.match(lines[0]):
            lines.pop(0)
    elif encoding.match(lines[1]):
        lines.pop(1)

    real_file = env.var('expand("%:p")')
    python_cmd = __get_virtualenv_python()
    if python_cmd:
        result = __run_with_external_python(python_cmd, lines, real_file)
        if result is not None:
            output, err = result
        else:
            python_cmd = None

    if not python_cmd:
        context = dict(
            __name__='__main__',
            __file__=real_file,
            input=env.user_input,
            raw_input=env.user_input)

        sys.stdout, stdout_ = StringIO(), sys.stdout
        sys.stderr, stderr_ = StringIO(), sys.stderr

        try:
            code = compile('\n'.join(lines) + '\n', env.curbuf.name, 'exec')
            sys.path.insert(0, env.curdir)
            exec(code, context) # noqa
            sys.path.pop(0)

        except SystemExit as e:
            if e.code:
                # A non-false code indicates abnormal termination.
                # A false code will be treated as a
                # successful run, and the error will be hidden from Vim
                sys.stdout, sys.stderr = stdout_, stderr_
                env.error("Script exited with code %s" % e.code)
                return env.stop()

        except Exception:
            import traceback
            err = traceback.format_exc()

        else:
            err = sys.stderr.getvalue()

        output = sys.stdout.getvalue()
        sys.stdout, sys.stderr = stdout_, stderr_

    output = env.prepare_value(output, dumps=False)

    errors += [er for er in err.splitlines() if er and "<string>" not in er]

    env.let('l:traceback', errors[2:])
    env.let('l:output', [s for s in output.splitlines()])


def __get_virtualenv_python():
    path = env.var('g:pymode_virtualenv_enabled', silence=True, default='')
    if not path:
        return None

    if os.name == 'nt':
        candidates = [
            os.path.join(path, 'Scripts', 'python.exe'),
            os.path.join(path, 'Scripts', 'python'),
        ]
    else:
        candidates = [os.path.join(path, 'bin', 'python')]

    for candidate in candidates:
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate

    return None


def __run_with_external_python(python_cmd, lines, real_file):
    # Inject __file__ so user code sees the real source path, not the temp file
    header = '__file__ = %r\n' % real_file
    source = header + '\n'.join(lines) + '\n'
    temp_file_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.py', delete=False, encoding='utf-8'
        ) as temp_file:
            temp_file.write(source)
            temp_file_path = temp_file.name

        timeout = env.var('g:pymode_run_timeout', silence=True, default=0) or None
        process = subprocess.Popen(
            [python_cmd, temp_file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=env.curdir,
            text=True,
            encoding='utf-8')
        try:
            output, err = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            output, err = process.communicate()
            err += '\nProcess timed out after %s second(s).' % timeout
    except OSError as exc:
        env.debug('Failed to execute external python', python_cmd, exc)
        return None
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

    # Replace temp path in tracebacks so errors reference the real source file
    if temp_file_path:
        err = err.replace(temp_file_path, real_file)

    return output, err


def __prepare_lines(line1, line2):

    lines = [l.rstrip() for l in env.lines[int(line1) - 1:int(line2)]]

    indent = 0
    for line in lines:
        if line:
            indent = len(line) - len(line.lstrip())
            break

    if len(lines) == 1:
        lines.append('')
    return [l[indent:] for l in lines]
