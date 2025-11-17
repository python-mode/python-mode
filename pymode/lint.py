"""Ruff integration for python-mode linting."""

from .environment import env
from .ruff_integration import run_ruff_check, check_ruff_available, validate_configuration

import os.path


def code_check():
    """Run ruff check on current file.

    This function replaces the previous pylama integration with ruff.
    It maintains compatibility with existing pymode configuration variables.

    :return bool:

    """
    if not env.curbuf.name:
        return env.stop()

    # Check if Ruff is enabled
    if not env.var('g:pymode_ruff_enabled', silence=True, default=True):
        return env.stop()

    # Check if ruff is available
    if not check_ruff_available():
        env.error("Ruff is not available. Please install ruff: pip install ruff")
        return env.stop()

    # Validate configuration and show warnings
    warnings = validate_configuration()
    for warning in warnings:
        env.message(f"Warning: {warning}")

    # Get file content from current buffer
    content = '\n'.join(env.curbuf) + '\n'
    file_path = env.curbuf.name

    # Use relpath if possible, but handle Windows drive letter differences
    try:
        path = os.path.relpath(file_path, env.curdir)
        env.debug("Start ruff code check: ", path)
    except ValueError:
        # On Windows, relpath fails if paths are on different drives
        # Fall back to absolute path in this case
        env.debug("Start ruff code check (abs path): ", file_path)
        path = file_path

    # Run ruff check
    errors = run_ruff_check(file_path, content)

    env.debug("Find errors: ", len(errors))
    
    # Apply sorting if configured
    sort_rules = env.var('g:pymode_lint_sort', default=[])

    def __sort(e):
        try:
            return sort_rules.index(e.get('type'))
        except ValueError:
            return 999

    if sort_rules:
        env.debug("Find sorting: ", sort_rules)
        errors = sorted(errors, key=__sort)

    # Convert to vim-compatible format
    errors_list = []
    for error in errors:
        err_dict = error.to_dict()
        err_dict['bufnr'] = env.curbuf.number
        errors_list.append(err_dict)

    # Add to location list
    env.run('g:PymodeLocList.current().extend', errors_list)

# ruff: noqa
