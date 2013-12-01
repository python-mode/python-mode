""" Support virtualenv in pymode. """

import os.path
import vim # noqa

from .utils import pymode_message, catch_and_print_exceptions


@catch_and_print_exceptions
def enable_virtualenv():
    """ Enable virtualenv for vim.

    :return bool:

    """

    path = vim.eval('g:pymode_virtualenv_path')
    enabled = vim.eval('g:pymode_virtualenv_enabled')
    if path == enabled:
        pymode_message('Virtualenv %s already enabled.' % path)
        return False

    activate_this = os.path.join(os.path.join(path, 'bin'), 'activate_this.py')

    # Fix for windows
    if not os.path.exists(activate_this):
        activate_this = os.path.join(
            os.path.join(path, 'Scripts'), 'activate_this.py')

    f = open(activate_this)
    try:
        source = f.read()
        exec(compile(  # noqa
            source, activate_this, 'exec'), dict(__file__=activate_this))
        pymode_message('Activate virtualenv: ' + path)
        vim.command('let g:pymode_virtualenv_enabled = "%s"' % path)
        return True
    finally:
        f.close()
