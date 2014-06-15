""" Load extensions. """

from os import listdir, path as op


CURDIR = op.dirname(__file__)
LINTERS = dict()
PREFIX = 'pylama_'

try:
    from importlib import import_module
except ImportError:
    from ..libs.importlib import import_module

for p in listdir(CURDIR):
    if p.startswith(PREFIX) and op.isdir(op.join(CURDIR, p)):
        name = p[len(PREFIX):]
        try:
            module = import_module('.lint.%s%s' % (PREFIX, name), 'pylama')
            LINTERS[name] = getattr(module, 'Linter')()
        except ImportError:
            continue

try:
    from pkg_resources import iter_entry_points

    for entry in iter_entry_points('pylama.linter'):
        if entry.name not in LINTERS:
            LINTERS[entry.name] = entry.load()()
except ImportError:
    pass
