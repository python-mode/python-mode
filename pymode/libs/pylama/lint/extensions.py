"""Load extensions."""

LINTERS = {}

try:
    from pylama.lint.pylama_mccabe import Linter
    LINTERS['mccabe'] = Linter()
except ImportError:
    pass

try:
    from pylama.lint.pylama_pep257 import Linter
    LINTERS['pep257'] = Linter()
except ImportError:
    pass

try:
    from pylama.lint.pylama_pep8 import Linter
    LINTERS['pep8'] = Linter()
except ImportError:
    pass

try:
    from pylama.lint.pylama_pyflakes import Linter
    LINTERS['pyflakes'] = Linter()
except ImportError:
    pass


from pkg_resources import iter_entry_points

for entry in iter_entry_points('pylama.linter'):
    if entry.name not in LINTERS:
        try:
            LINTERS[entry.name] = entry.load()()
        except ImportError:
            pass

#  pylama:ignore=E0611
