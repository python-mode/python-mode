""" Support virtualenv in pymode. """

import os.path

from .environment import env


@env.catch_exceptions
def enable_virtualenv():
    """ Enable virtualenv for vim.

    :return bool:

    """
    path = env.var('g:pymode_virtualenv_path')
    enabled = env.var('g:pymode_virtualenv_enabled')
    if path == enabled:
        env.message('Virtualenv %s already enabled.' % path)
        return env.stop()

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
        env.message('Activate virtualenv: ' + path)
        env.let('g:pymode_virtualenv_enabled', path)
        return True
    finally:
        f.close()
