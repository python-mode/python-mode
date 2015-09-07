"""Astroid hooks for pytest."""

from astroid import MANAGER, register_module_extender
from astroid.builder import AstroidBuilder


def pytest_transform():
    return AstroidBuilder(MANAGER).string_build('''

try:
    import _pytest.mark
    import _pytest.recwarn
    import _pytest.runner
    import _pytest.python
except ImportError:
    pass
else:
    deprecated_call = _pytest.recwarn.deprecated_call
    exit = _pytest.runner.exit
    fail = _pytest.runner.fail
    fixture = _pytest.python.fixture
    importorskip = _pytest.runner.importorskip
    mark = _pytest.mark.MarkGenerator()
    raises = _pytest.python.raises
    skip = _pytest.runner.skip
    yield_fixture = _pytest.python.yield_fixture

''')

register_module_extender(MANAGER, 'pytest', pytest_transform)
register_module_extender(MANAGER, 'py.test', pytest_transform)
