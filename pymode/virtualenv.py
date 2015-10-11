""" Support virtualenv in pymode. """

import os
import sys
import site

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

    try:
        with open(activate_this) as f:
            source = f.read()
            exec(compile(  # noqa
                source, activate_this, 'exec'), dict(__file__=activate_this))
    except IOError:
        _activate_env_from_path(path)

    env.message('Activate virtualenv: ' + path)
    env.let('g:pymode_virtualenv_enabled', path)
    return True


def _activate_env_from_path(env_path):
    """ Fix when `activate_this.py` does not exist.

        For Python 3.3 and newer, a new command-line tool `pyvenv` create venv
        will not provide 'activate_this.py'.
    """
    prev_sys_path = list(sys.path)

    if sys.platform == 'win32':
        site_packages_paths = [os.path.join(env_path, 'Lib', 'site-packages')]
    else:
        lib_path = os.path.join(env_path, 'lib')
        site_packages_paths = [os.path.join(lib_path, lib, 'site-packages')
                               for lib in os.listdir(lib_path)]
    for site_packages_path in site_packages_paths:
        site.addsitedir(site_packages_path)

    sys.real_prefix = sys.prefix
    sys.prefix = env_path
    sys.exec_prefix = env_path

    # Move the added items to the front of the path:
    new_sys_path = []
    for item in list(sys.path):
        if item not in prev_sys_path:
            new_sys_path.append(item)
            sys.path.remove(item)
    sys.path[:0] = new_sys_path
