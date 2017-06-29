
"""Astroid hooks for the Python 2 standard library.

Currently help understanding of :

* hashlib.md5 and hashlib.sha1
"""

import functools
import sys
from textwrap import dedent

from astroid import (
    MANAGER, UseInferenceDefault, inference_tip, BoundMethod,
    InferenceError, register_module_extender)
from astroid import exceptions
from astroid import nodes
from astroid.builder import AstroidBuilder
from astroid import util
from astroid import test_utils

PY3K = sys.version_info > (3, 0)
PY33 = sys.version_info >= (3, 3)
PY34 = sys.version_info >= (3, 4)

# general function

def infer_func_form(node, base_type, context=None, enum=False):
    """Specific inference function for namedtuple or Python 3 enum. """
    def infer_first(node):
        if node is util.YES:
            raise UseInferenceDefault
        try:            
            value = next(node.infer(context=context))
            if value is util.YES:
                raise UseInferenceDefault()
            else:
                return value
        except StopIteration:
            raise InferenceError()

    # node is a Call node, class name as first argument and generated class
    # attributes as second argument
    if len(node.args) != 2:
        # something weird here, go back to class implementation
        raise UseInferenceDefault()
    # namedtuple or enums list of attributes can be a list of strings or a
    # whitespace-separate string
    try:
        name = infer_first(node.args[0]).value
        names = infer_first(node.args[1])
        try:
            attributes = names.value.replace(',', ' ').split()
        except AttributeError:
            if not enum:
                attributes = [infer_first(const).value for const in names.elts]
            else:
                # Enums supports either iterator of (name, value) pairs
                # or mappings.
                # TODO: support only list, tuples and mappings.
                if hasattr(names, 'items') and isinstance(names.items, list):
                    attributes = [infer_first(const[0]).value
                                  for const in names.items
                                  if isinstance(const[0], nodes.Const)]
                elif hasattr(names, 'elts'):
                    # Enums can support either ["a", "b", "c"]
                    # or [("a", 1), ("b", 2), ...], but they can't
                    # be mixed.
                    if all(isinstance(const, nodes.Tuple)
                           for const in names.elts):
                        attributes = [infer_first(const.elts[0]).value
                                      for const in names.elts
                                      if isinstance(const, nodes.Tuple)]
                    else:
                        attributes = [infer_first(const).value
                                      for const in names.elts]
                else:
                    raise AttributeError
                if not attributes:
                    raise AttributeError
    except (AttributeError, exceptions.InferenceError):
        raise UseInferenceDefault()

    # If we can't iner the name of the class, don't crash, up to this point
    # we know it is a namedtuple anyway.
    name = name or 'Uninferable'
    # we want to return a Class node instance with proper attributes set
    class_node = nodes.ClassDef(name, 'docstring')
    class_node.parent = node.parent
    # set base class=tuple
    class_node.bases.append(base_type)
    # XXX add __init__(*attributes) method
    for attr in attributes:
        fake_node = nodes.EmptyNode()
        fake_node.parent = class_node
        fake_node.attrname = attr
        class_node._instance_attrs[attr] = [fake_node]
    return class_node, name, attributes


# module specific transformation functions #####################################

def hashlib_transform():
    template = '''

class %(name)s(object):
  def __init__(self, value=''): pass
  def digest(self):
    return %(digest)s
  def copy(self):
    return self
  def update(self, value): pass
  def hexdigest(self):
    return ''
  @property
  def name(self):
    return %(name)r
  @property
  def block_size(self):
    return 1
  @property
  def digest_size(self):
    return 1
'''
    algorithms = ('md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512')
    classes = "".join(
        template % {'name': hashfunc, 'digest': 'b""' if PY3K else '""'}
        for hashfunc in algorithms)
    return AstroidBuilder(MANAGER).string_build(classes)


def collections_transform():
    return AstroidBuilder(MANAGER).string_build('''

class defaultdict(dict):
    default_factory = None
    def __missing__(self, key): pass

class deque(object):
    maxlen = 0
    def __init__(self, iterable=None, maxlen=None):
        self.iterable = iterable
    def append(self, x): pass
    def appendleft(self, x): pass
    def clear(self): pass
    def count(self, x): return 0
    def extend(self, iterable): pass
    def extendleft(self, iterable): pass
    def pop(self): pass
    def popleft(self): pass
    def remove(self, value): pass
    def reverse(self): pass
    def rotate(self, n): pass
    def __iter__(self): return self
    def __reversed__(self): return self.iterable[::-1]
    def __getitem__(self, index): pass
    def __setitem__(self, index, value): pass
    def __delitem__(self, index): pass
''')


def pkg_resources_transform():
    return AstroidBuilder(MANAGER).string_build('''
def require(*requirements):
    return pkg_resources.working_set.require(*requirements)

def run_script(requires, script_name):
    return pkg_resources.working_set.run_script(requires, script_name)

def iter_entry_points(group, name=None):
    return pkg_resources.working_set.iter_entry_points(group, name)

def resource_exists(package_or_requirement, resource_name):
    return get_provider(package_or_requirement).has_resource(resource_name)

def resource_isdir(package_or_requirement, resource_name):
    return get_provider(package_or_requirement).resource_isdir(
        resource_name)

def resource_filename(package_or_requirement, resource_name):
    return get_provider(package_or_requirement).get_resource_filename(
        self, resource_name)

def resource_stream(package_or_requirement, resource_name):
    return get_provider(package_or_requirement).get_resource_stream(
        self, resource_name)

def resource_string(package_or_requirement, resource_name):
    return get_provider(package_or_requirement).get_resource_string(
        self, resource_name)

def resource_listdir(package_or_requirement, resource_name):
    return get_provider(package_or_requirement).resource_listdir(
        resource_name)

def extraction_error():
    pass

def get_cache_path(archive_name, names=()):
    extract_path = self.extraction_path or get_default_cache()
    target_path = os.path.join(extract_path, archive_name+'-tmp', *names)
    return target_path

def postprocess(tempname, filename):
    pass

def set_extraction_path(path):
    pass

def cleanup_resources(force=False):
    pass

''')


def subprocess_transform():
    if PY3K:
        communicate = (bytes('string', 'ascii'), bytes('string', 'ascii'))
        communicate_signature = 'def communicate(self, input=None, timeout=None)'
        init = """
        def __init__(self, args, bufsize=0, executable=None,
                     stdin=None, stdout=None, stderr=None,
                     preexec_fn=None, close_fds=False, shell=False,
                     cwd=None, env=None, universal_newlines=False,
                     startupinfo=None, creationflags=0, restore_signals=True,
                     start_new_session=False, pass_fds=()):
            pass
        """
    else:
        communicate = ('string', 'string')
        communicate_signature = 'def communicate(self, input=None)'
        init = """
        def __init__(self, args, bufsize=0, executable=None,
                     stdin=None, stdout=None, stderr=None,
                     preexec_fn=None, close_fds=False, shell=False,
                     cwd=None, env=None, universal_newlines=False,
                     startupinfo=None, creationflags=0):
            pass
        """
    if PY33:
        wait_signature = 'def wait(self, timeout=None)'
    else:
        wait_signature = 'def wait(self)'
    if PY3K:
        ctx_manager = '''
        def __enter__(self): return self
        def __exit__(self, *args): pass
        '''
    else:
        ctx_manager = ''
    code = dedent('''

    class Popen(object):
        returncode = pid = 0
        stdin = stdout = stderr = file()

        %(init)s

        %(communicate_signature)s:
            return %(communicate)r
        %(wait_signature)s:
            return self.returncode
        def poll(self):
            return self.returncode
        def send_signal(self, signal):
            pass
        def terminate(self):
            pass
        def kill(self):
            pass
        %(ctx_manager)s
       ''' % {'init': init,
              'communicate': communicate,
              'communicate_signature': communicate_signature,
              'wait_signature': wait_signature,
              'ctx_manager': ctx_manager})
    return AstroidBuilder(MANAGER).string_build(code)


# namedtuple support ###########################################################

def _looks_like(node, name):
    func = node.func
    if isinstance(func, nodes.Attribute):
        return func.attrname == name
    if isinstance(func, nodes.Name):
        return func.name == name
    return False

_looks_like_namedtuple = functools.partial(_looks_like, name='namedtuple')
_looks_like_enum = functools.partial(_looks_like, name='Enum')


def infer_named_tuple(node, context=None):
    """Specific inference function for namedtuple Call node"""
    class_node, name, attributes = infer_func_form(node, nodes.Tuple._proxied,
                                                   context=context)
    fake = AstroidBuilder(MANAGER).string_build('''
class %(name)s(tuple):
    _fields = %(fields)r
    def _asdict(self):
        return self.__dict__
    @classmethod
    def _make(cls, iterable, new=tuple.__new__, len=len):
        return new(cls, iterable)
    def _replace(self, **kwds):
        return self
    ''' % {'name': name, 'fields': attributes})
    class_node._locals['_asdict'] = fake.body[0]._locals['_asdict']
    class_node._locals['_make'] = fake.body[0]._locals['_make']
    class_node._locals['_replace'] = fake.body[0]._locals['_replace']
    class_node._locals['_fields'] = fake.body[0]._locals['_fields']
    # we use UseInferenceDefault, we can't be a generator so return an iterator
    return iter([class_node])


def infer_enum(node, context=None):
    """ Specific inference function for enum Call node. """
    enum_meta = test_utils.extract_node('''
    class EnumMeta(object):
        'docstring'
        def __call__(self, node):
            class EnumAttribute(object):
                name = ''
                value = 0
            return EnumAttribute()
    ''')
    class_node = infer_func_form(node, enum_meta,
                                 context=context, enum=True)[0]
    return iter([class_node.instantiate_class()])


def infer_enum_class(node):
    """ Specific inference for enums. """
    names = set(('Enum', 'IntEnum', 'enum.Enum', 'enum.IntEnum'))
    for basename in node.basenames:
        # TODO: doesn't handle subclasses yet. This implementation
        # is a hack to support enums.
        if basename not in names:
            continue
        if node.root().name == 'enum':
            # Skip if the class is directly from enum module.
            break
        for local, values in node._locals.items():
            if any(not isinstance(value, nodes.AssignName)
                   for value in values):
                continue

            stmt = values[0].statement()
            if isinstance(stmt.targets[0], nodes.Tuple):
                targets = stmt.targets[0].itered()
            else:
                targets = stmt.targets

            new_targets = []
            for target in targets:
                # Replace all the assignments with our mocked class.
                classdef = dedent('''
                class %(name)s(%(types)s):
                    @property
                    def value(self):
                        # Not the best return.
                        return None
                    @property
                    def name(self):
                        return %(name)r
                ''' % {'name': target.name, 'types': ', '.join(node.basenames)})
                fake = AstroidBuilder(MANAGER).string_build(classdef)[target.name]
                fake.parent = target.parent
                for method in node.mymethods():
                    fake._locals[method.name] = [method]
                new_targets.append(fake.instantiate_class())
            node._locals[local] = new_targets
        break
    return node

def multiprocessing_transform():
    module = AstroidBuilder(MANAGER).string_build(dedent('''
    from multiprocessing.managers import SyncManager
    def Manager():
        return SyncManager()
    '''))
    if not PY34:
        return module

    # On Python 3.4, multiprocessing uses a getattr lookup inside contexts,
    # in order to get the attributes they need. Since it's extremely
    # dynamic, we use this approach to fake it.
    node = AstroidBuilder(MANAGER).string_build(dedent('''
    from multiprocessing.context import DefaultContext, BaseContext
    default = DefaultContext()
    base = BaseContext()
    '''))
    try:
        context = next(node['default'].infer())
        base = next(node['base'].infer())
    except InferenceError:
        return module

    for node in (context, base):
        for key, value in node._locals.items():
            if key.startswith("_"):
                continue

            value = value[0]
            if isinstance(value, nodes.FunctionDef):
                # We need to rebound this, since otherwise
                # it will have an extra argument (self).
                value = BoundMethod(value, node)
            module[key] = value
    return module

def multiprocessing_managers_transform():
    return AstroidBuilder(MANAGER).string_build(dedent('''
    import array
    import threading
    import multiprocessing.pool as pool

    import six

    class Namespace(object):
        pass

    class Value(object):
        def __init__(self, typecode, value, lock=True):
            self._typecode = typecode
            self._value = value
        def get(self):
            return self._value
        def set(self, value):
            self._value = value
        def __repr__(self):
            return '%s(%r, %r)'%(type(self).__name__, self._typecode, self._value)
        value = property(get, set)

    def Array(typecode, sequence, lock=True):
        return array.array(typecode, sequence)

    class SyncManager(object):
        Queue = JoinableQueue = six.moves.queue.Queue
        Event = threading.Event
        RLock = threading.RLock
        BoundedSemaphore = threading.BoundedSemaphore
        Condition = threading.Condition
        Barrier = threading.Barrier
        Pool = pool.Pool
        list = list
        dict = dict
        Value = Value
        Array = Array
        Namespace = Namespace
        __enter__ = lambda self: self
        __exit__ = lambda *args: args
        
        def start(self, initializer=None, initargs=None):
            pass
        def shutdown(self):
            pass
    '''))


MANAGER.register_transform(nodes.Call, inference_tip(infer_named_tuple),
                           _looks_like_namedtuple)
MANAGER.register_transform(nodes.Call, inference_tip(infer_enum),
                           _looks_like_enum)
MANAGER.register_transform(nodes.ClassDef, infer_enum_class)
register_module_extender(MANAGER, 'hashlib', hashlib_transform)
register_module_extender(MANAGER, 'collections', collections_transform)
register_module_extender(MANAGER, 'pkg_resources', pkg_resources_transform)
register_module_extender(MANAGER, 'subprocess', subprocess_transform)
register_module_extender(MANAGER, 'multiprocessing.managers',
                         multiprocessing_managers_transform)
register_module_extender(MANAGER, 'multiprocessing', multiprocessing_transform)
