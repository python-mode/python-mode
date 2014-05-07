"""Astroid hooks for the Python 2 standard library.

Currently help understanding of :

* hashlib.md5 and hashlib.sha1
"""

import sys

from astroid import MANAGER, AsStringRegexpPredicate, UseInferenceDefault, inference_tip, YES
from astroid import exceptions
from astroid import nodes
from astroid.builder import AstroidBuilder

MODULE_TRANSFORMS = {}
PY3K = sys.version_info > (3, 0)


# module specific transformation functions #####################################

def transform(module):
    try:
        tr = MODULE_TRANSFORMS[module.name]
    except KeyError:
        pass
    else:
        tr(module)
MANAGER.register_transform(nodes.Module, transform)

# module specific transformation functions #####################################

def hashlib_transform(module):
    template = '''

class %s(object):
  def __init__(self, value=''): pass
  def digest(self):
    return u''
  def update(self, value): pass
  def hexdigest(self):
    return u''
'''

    algorithms = ('md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512')
    classes = "".join(template % hashfunc for hashfunc in algorithms)

    fake = AstroidBuilder(MANAGER).string_build(classes)

    for hashfunc in algorithms:
        module.locals[hashfunc] = fake.locals[hashfunc]

def collections_transform(module):
    fake = AstroidBuilder(MANAGER).string_build('''

class defaultdict(dict):
    default_factory = None
    def __missing__(self, key): pass

class deque(object):
    maxlen = 0
    def __init__(iterable=None, maxlen=None): pass
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

    for klass in ('deque', 'defaultdict'):
        module.locals[klass] = fake.locals[klass]

def pkg_resources_transform(module):
    fake = AstroidBuilder(MANAGER).string_build('''

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

    for func_name, func in fake.locals.items():
        module.locals[func_name] = func


def urlparse_transform(module):
    fake = AstroidBuilder(MANAGER).string_build('''

def urlparse(url, scheme='', allow_fragments=True):
    return ParseResult()

class ParseResult(object):
    def __init__(self):
        self.scheme = ''
        self.netloc = ''
        self.path = ''
        self.params = ''
        self.query = ''
        self.fragment = ''
        self.username = None
        self.password = None
        self.hostname = None
        self.port = None

    def geturl(self):
        return ''
''')

    for func_name, func in fake.locals.items():
        module.locals[func_name] = func

def subprocess_transform(module):
    if PY3K:
        communicate = (bytes('string', 'ascii'), bytes('string', 'ascii'))
    else:
        communicate = ('string', 'string')
    fake = AstroidBuilder(MANAGER).string_build('''

class Popen(object):
    returncode = pid = 0
    stdin = stdout = stderr = file()

    def __init__(self, args, bufsize=0, executable=None,
                 stdin=None, stdout=None, stderr=None,
                 preexec_fn=None, close_fds=False, shell=False,
                 cwd=None, env=None, universal_newlines=False,
                 startupinfo=None, creationflags=0):
        pass

    def communicate(self, input=None):
        return %r
    def wait(self):
        return self.returncode
    def poll(self):
        return self.returncode
    def send_signal(self, signal):
        pass
    def terminate(self):
        pass
    def kill(self):
        pass
   ''' % (communicate, ))

    for func_name, func in fake.locals.items():
        module.locals[func_name] = func



MODULE_TRANSFORMS['hashlib'] = hashlib_transform
MODULE_TRANSFORMS['collections'] = collections_transform
MODULE_TRANSFORMS['pkg_resources'] = pkg_resources_transform
MODULE_TRANSFORMS['urlparse'] = urlparse_transform
MODULE_TRANSFORMS['subprocess'] = subprocess_transform

# namedtuple support ###########################################################

def infer_named_tuple(node, context=None):
    """Specific inference function for namedtuple CallFunc node"""
    def infer_first(node):
        try:
            value = node.infer().next()
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
    # namedtuple list of attributes can be a list of strings or a
    # whitespace-separate string
    try:
        name = infer_first(node.args[0]).value
        names = infer_first(node.args[1])
        try:
            attributes = names.value.split()
        except AttributeError:
            attributes = [infer_first(const).value for const in names.elts]
    except (AttributeError, exceptions.InferenceError):
        raise UseInferenceDefault()
    # we want to return a Class node instance with proper attributes set
    class_node = nodes.Class(name, 'docstring')
    class_node.parent = node.parent
    # set base class=tuple
    class_node.bases.append(nodes.Tuple._proxied)
    # XXX add __init__(*attributes) method
    for attr in attributes:
        fake_node = nodes.EmptyNode()
        fake_node.parent = class_node
        class_node.instance_attrs[attr] = [fake_node]

    fake = AstroidBuilder(MANAGER).string_build('''
class %(name)s(tuple):
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
    # we use UseInferenceDefault, we can't be a generator so return an iterator
    return iter([class_node])

MANAGER.register_transform(nodes.CallFunc, inference_tip(infer_named_tuple),
                           AsStringRegexpPredicate('namedtuple', 'func'))
