"""Astroid hooks for various builtins."""

import sys
from functools import partial
from textwrap import dedent

import six
from astroid import (MANAGER, UseInferenceDefault,
                     inference_tip, YES, InferenceError, UnresolvableName)
from astroid import arguments
from astroid import nodes
from astroid import objects
from astroid.builder import AstroidBuilder
from astroid import util

def _extend_str(class_node, rvalue):
    """function to extend builtin str/unicode class"""
    # TODO(cpopa): this approach will make astroid to believe
    # that some arguments can be passed by keyword, but
    # unfortunately, strings and bytes don't accept keyword arguments.
    code = dedent('''
    class whatever(object):
        def join(self, iterable):
            return {rvalue}
        def replace(self, old, new, count=None):
            return {rvalue}
        def format(self, *args, **kwargs):
            return {rvalue}
        def encode(self, encoding='ascii', errors=None):
            return ''
        def decode(self, encoding='ascii', errors=None):
            return u''
        def capitalize(self):
            return {rvalue}
        def title(self):
            return {rvalue}
        def lower(self):
            return {rvalue}
        def upper(self):
            return {rvalue}
        def swapcase(self):
            return {rvalue}
        def index(self, sub, start=None, end=None):
            return 0
        def find(self, sub, start=None, end=None):
            return 0
        def count(self, sub, start=None, end=None):
            return 0
        def strip(self, chars=None):
            return {rvalue}
        def lstrip(self, chars=None):
            return {rvalue}
        def rstrip(self, chars=None):
            return {rvalue}
        def rjust(self, width, fillchar=None):
            return {rvalue}
        def center(self, width, fillchar=None):
            return {rvalue}
        def ljust(self, width, fillchar=None):
            return {rvalue}
    ''')
    code = code.format(rvalue=rvalue)
    fake = AstroidBuilder(MANAGER).string_build(code)['whatever']
    for method in fake.mymethods():
        class_node._locals[method.name] = [method]
        method.parent = class_node

def extend_builtins(class_transforms):
    from astroid.bases import BUILTINS
    builtin_ast = MANAGER.astroid_cache[BUILTINS]
    for class_name, transform in class_transforms.items():
        transform(builtin_ast[class_name])

if sys.version_info > (3, 0):
    extend_builtins({'bytes': partial(_extend_str, rvalue="b''"),
                     'str': partial(_extend_str, rvalue="''")})
else:
    extend_builtins({'str': partial(_extend_str, rvalue="''"),
                     'unicode': partial(_extend_str, rvalue="u''")})


def register_builtin_transform(transform, builtin_name):
    """Register a new transform function for the given *builtin_name*.

    The transform function must accept two parameters, a node and
    an optional context.
    """
    def _transform_wrapper(node, context=None):
        result = transform(node, context=context)
        if result:
            if not result.parent:
                # Let the transformation function determine
                # the parent for its result. Otherwise,
                # we set it to be the node we transformed from.
                result.parent = node

            result.lineno = node.lineno
            result.col_offset = node.col_offset
        return iter([result])

    MANAGER.register_transform(nodes.Call,
                               inference_tip(_transform_wrapper),
                               lambda n: (isinstance(n.func, nodes.Name) and
                                          n.func.name == builtin_name))


def _generic_inference(node, context, node_type, transform):
    args = node.args
    if not args:
        return node_type()
    if len(node.args) > 1:
        raise UseInferenceDefault()

    arg, = args
    transformed = transform(arg)
    if not transformed:
        try:
            inferred = next(arg.infer(context=context))
        except (InferenceError, StopIteration):
            raise UseInferenceDefault()
        if inferred is util.YES:
            raise UseInferenceDefault()
        transformed = transform(inferred)
    if not transformed or transformed is util.YES:
        raise UseInferenceDefault()
    return transformed


def _generic_transform(arg, klass, iterables, build_elts):
    if isinstance(arg, klass):
        return arg
    elif isinstance(arg, iterables):
        if not all(isinstance(elt, nodes.Const)
                   for elt in arg.elts):
            # TODO(cpopa): Don't support heterogenous elements.
            # Not yet, though.
            raise UseInferenceDefault()
        elts = [elt.value for elt in arg.elts]
    elif isinstance(arg, nodes.Dict):
        if not all(isinstance(elt[0], nodes.Const)
                   for elt in arg.items):
            raise UseInferenceDefault()
        elts = [item[0].value for item in arg.items]
    elif (isinstance(arg, nodes.Const) and
          isinstance(arg.value, (six.string_types, six.binary_type))):
        elts = arg.value
    else:
        return
    return klass(elts=build_elts(elts))


def _infer_builtin(node, context,
                   klass=None, iterables=None,
                   build_elts=None):
    transform_func = partial(
        _generic_transform,
        klass=klass,
        iterables=iterables,
        build_elts=build_elts)

    return _generic_inference(node, context, klass, transform_func)

# pylint: disable=invalid-name
infer_tuple = partial(
    _infer_builtin,
    klass=nodes.Tuple,
    iterables=(nodes.List, nodes.Set),
    build_elts=tuple)

infer_list = partial(
    _infer_builtin,
    klass=nodes.List,
    iterables=(nodes.Tuple, nodes.Set),
    build_elts=list)

infer_set = partial(
    _infer_builtin,
    klass=nodes.Set,
    iterables=(nodes.List, nodes.Tuple),
    build_elts=set)

infer_frozenset = partial(
    _infer_builtin,
    klass=objects.FrozenSet,
    iterables=(nodes.List, nodes.Tuple, nodes.Set),
    build_elts=frozenset)


def _get_elts(arg, context):
    is_iterable = lambda n: isinstance(n,
                                       (nodes.List, nodes.Tuple, nodes.Set))
    try:
        inferred = next(arg.infer(context))
    except (InferenceError, UnresolvableName):
        raise UseInferenceDefault()
    if isinstance(inferred, nodes.Dict):
        items = inferred.items
    elif is_iterable(inferred):
        items = []
        for elt in inferred.elts:
            # If an item is not a pair of two items,
            # then fallback to the default inference.
            # Also, take in consideration only hashable items,
            # tuples and consts. We are choosing Names as well.
            if not is_iterable(elt):
                raise UseInferenceDefault()
            if len(elt.elts) != 2:
                raise UseInferenceDefault()
            if not isinstance(elt.elts[0],
                              (nodes.Tuple, nodes.Const, nodes.Name)):
                raise UseInferenceDefault()
            items.append(tuple(elt.elts))
    else:
        raise UseInferenceDefault()
    return items

def infer_dict(node, context=None):
    """Try to infer a dict call to a Dict node.

    The function treats the following cases:

        * dict()
        * dict(mapping)
        * dict(iterable)
        * dict(iterable, **kwargs)
        * dict(mapping, **kwargs)
        * dict(**kwargs)

    If a case can't be inferred, we'll fallback to default inference.
    """
    call = arguments.CallSite.from_call(node)
    if call.has_invalid_arguments() or call.has_invalid_keywords():
        raise UseInferenceDefault

    args = call.positional_arguments
    kwargs = list(call.keyword_arguments.items())

    if not args and not kwargs:
        # dict()
        return nodes.Dict()
    elif kwargs and not args:
        # dict(a=1, b=2, c=4)
        items = [(nodes.Const(key), value) for key, value in kwargs]
    elif len(args) == 1 and kwargs:
        # dict(some_iterable, b=2, c=4)
        elts = _get_elts(args[0], context)
        keys = [(nodes.Const(key), value) for key, value in kwargs]
        items = elts + keys
    elif len(args) == 1:
        items = _get_elts(args[0], context)
    else:
        raise UseInferenceDefault()

    empty = nodes.Dict()
    empty.items = items
    return empty


def _node_class(node):
    klass = node.frame()
    while klass is not None and not isinstance(klass, nodes.ClassDef):
        if klass.parent is None:
            klass = None
        else:
            klass = klass.parent.frame()
    return klass


def infer_super(node, context=None):
    """Understand super calls.

    There are some restrictions for what can be understood:

        * unbounded super (one argument form) is not understood.

        * if the super call is not inside a function (classmethod or method),
          then the default inference will be used.

        * if the super arguments can't be infered, the default inference
          will be used.
    """
    if len(node.args) == 1:
        # Ignore unbounded super.
        raise UseInferenceDefault

    scope = node.scope()
    if not isinstance(scope, nodes.FunctionDef):
        # Ignore non-method uses of super.
        raise UseInferenceDefault
    if scope.type not in ('classmethod', 'method'):
        # Not interested in staticmethods.
        raise UseInferenceDefault

    cls = _node_class(scope)
    if not len(node.args):
        mro_pointer = cls
        # In we are in a classmethod, the interpreter will fill
        # automatically the class as the second argument, not an instance.
        if scope.type == 'classmethod':
            mro_type = cls
        else:
            mro_type = cls.instantiate_class()
    else:
        # TODO(cpopa): support flow control (multiple inference values).
        try:
            mro_pointer = next(node.args[0].infer(context=context))
        except InferenceError:
            raise UseInferenceDefault
        try:
            mro_type = next(node.args[1].infer(context=context))
        except InferenceError:
            raise UseInferenceDefault

    if mro_pointer is YES or mro_type is YES:
        # No way we could understand this.
        raise UseInferenceDefault

    super_obj = objects.Super(mro_pointer=mro_pointer,
                              mro_type=mro_type,
                              self_class=cls,
                              scope=scope)
    super_obj.parent = node
    return iter([super_obj])


# Builtins inference
MANAGER.register_transform(nodes.Call,
                           inference_tip(infer_super),
                           lambda n: (isinstance(n.func, nodes.Name) and
                                      n.func.name == 'super'))

register_builtin_transform(infer_tuple, 'tuple')
register_builtin_transform(infer_set, 'set')
register_builtin_transform(infer_list, 'list')
register_builtin_transform(infer_dict, 'dict')
register_builtin_transform(infer_frozenset, 'frozenset')
