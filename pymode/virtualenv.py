"""Support virtualenv in pymode."""

import os
import sys
import site

from .environment import env


@env.catch_exceptions
def enable_virtualenv():
    """Enable virtualenv for vim.

    :return bool:

    """
    path = env.var('g:pymode_virtualenv_path')
    # Normalize path to be an absolute path
    # If an absolute path is provided, that path will be returned, otherwise
    # the returned path will be an absolute path but computed relative
    # to the current working directory
    path = os.path.abspath(path)
    enabled = env.var('g:pymode_virtualenv_enabled')
    if path == enabled:
        env.message('Virtualenv %s already enabled.' % path)
        return env.stop()

    activate_env_from_path(path)
    env.message('Activate virtualenv: ' + path)
    env.let('g:pymode_virtualenv_enabled', path)
    return True


def activate_env_from_path(env_path):
    """Activate given virtualenv."""
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
