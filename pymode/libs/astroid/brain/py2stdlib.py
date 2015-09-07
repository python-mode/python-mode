
"""Astroid hooks for the Python 2 standard library.

Currently help understanding of :

* hashlib.md5 and hashlib.sha1
"""

import sys
from functools import partial
from textwrap import dedent

from astroid import (
    MANAGER, AsStringRegexpPredicate,
    UseInferenceDefault, inference_tip,
    YES, InferenceError, register_module_extender)
from astroid import exceptions
from astroid import nodes
from astroid.builder import AstroidBuilder

PY3K = sys.version_info > (3, 0)
PY33 = sys.version_info >= (3, 3)

# general function

def infer_func_form(node, base_type, context=None, enum=False):
    """Specific inference function for namedtuple or Python 3 enum. """
    def infer_first(node):
        try:
            value = next(node.infer(context=context))
            if value is YES:
                raise UseInferenceDefault()
            else:
                return value
        except StopIteration:
            raise InferenceError()

    # node is a CallFunc node, class name as first argument and generated class
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
    except (AttributeError, exceptions.InferenceError) as exc:
        raise UseInferenceDefault()
    # we want to return a Class node instance with proper attributes set
    class_node = nodes.Class(name, 'docstring')
    class_node.parent = node.parent
    # set base class=tuple
    class_node.bases.append(base_type)
    # XXX add __init__(*attributes) method
    for attr in attributes:
        fake_node = nodes.EmptyNode()
        fake_node.parent = class_node
        class_node.instance_attrs[attr] = [fake_node]
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
    def __init__(self, iterable=None, maxlen=None): pass
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

''')


def pkg_resources_transform():
    return AstroidBuilder(MANAGER).string_build('''

def resource_exists(package_or_requirement, resource_name):
    pass

def resource_isdir(package_or_requirement, resource_name):
    pass

def resource_filename(package_or_requirement, resource_name):
    pass

def resource_stream(package_or_requirement, resource_name):
    pass

def resource_string(package_or_requirement, resource_name):
    pass

def resource_listdir(package_or_requirement, resource_name):
    pass

def extraction_error():
    pass

def get_cache_path(archive_name, names=()):
    pass

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
    return AstroidBuilder(MANAGER).string_build('''

class Popen(object):
    returncode = pid = 0
    stdin = stdout = stderr = file()

    %(init)s

    def communicate(self, input=None):
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
   ''' % {'init': init,
          'communicate': communicate,
          'wait_signature': wait_signature})


# namedtuple support ###########################################################

def looks_like_namedtuple(node):
    func = node.func
    if type(func) is nodes.Getattr:
        return func.attrname == 'namedtuple'
    if type(func) is nodes.Name:
        return func.name == 'namedtuple'
    return False

def infer_named_tuple(node, context=None):
    """Specific inference function for namedtuple CallFunc node"""
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
    def _replace(_self, **kwds):
        result = _self._make(map(kwds.pop, %(fields)r, _self))
        if kwds:
            raise ValueError('Got unexpected field names: %%r' %% list(kwds))
        return result
    ''' % {'name': name, 'fields': attributes})
    class_node.locals['_asdict'] = fake.body[0].locals['_asdict']
    class_node.locals['_make'] = fake.body[0].locals['_make']
    class_node.locals['_replace'] = fake.body[0].locals['_replace']
    class_node.locals['_fields'] = fake.body[0].locals['_fields']
    # we use UseInferenceDefault, we can't be a generator so return an iterator
    return iter([class_node])

def infer_enum(node, context=None):
    """ Specific inference function for enum CallFunc node. """
    enum_meta = nodes.Class("EnumMeta", 'docstring')
    class_node = infer_func_form(node, enum_meta,
                                 context=context, enum=True)[0]
    return iter([class_node.instanciate_class()])

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
        for local, values in node.locals.items():
            if any(not isinstance(value, nodes.AssName)
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
                class %(name)s(object):
                    @property
                    def value(self):
                        # Not the best return.
                        return None 
                    @property
                    def name(self):
                        return %(name)r
                ''' % {'name': target.name})
                fake = AstroidBuilder(MANAGER).string_build(classdef)[target.name]
                fake.parent = target.parent
                for method in node.mymethods():
                    fake.locals[method.name] = [method]
                new_targets.append(fake.instanciate_class())
            node.locals[local] = new_targets
        break
    return node


MANAGER.register_transform(nodes.CallFunc, inference_tip(infer_named_tuple),
                           looks_like_namedtuple)
MANAGER.register_transform(nodes.CallFunc, inference_tip(infer_enum),
                           AsStringRegexpPredicate('Enum', 'func'))
MANAGER.register_transform(nodes.Class, infer_enum_class)
register_module_extender(MANAGER, 'hashlib', hashlib_transform)
register_module_extender(MANAGER, 'collections', collections_transform)
register_module_extender(MANAGER, 'pkg_resources', pkg_resources_transform)
register_module_extender(MANAGER, 'subprocess', subprocess_transform)
