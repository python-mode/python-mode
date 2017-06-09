"""Utility functions for test code that uses astroid ASTs as input."""
import functools
import sys

from astroid import nodes
from astroid import builder
# The name of the transient function that is used to
# wrap expressions to be extracted when calling
# extract_node.
_TRANSIENT_FUNCTION = '__'

# The comment used to select a statement to be extracted
# when calling extract_node.
_STATEMENT_SELECTOR = '#@'

def _extract_expressions(node):
    """Find expressions in a call to _TRANSIENT_FUNCTION and extract them.

    The function walks the AST recursively to search for expressions that
    are wrapped into a call to _TRANSIENT_FUNCTION. If it finds such an
    expression, it completely removes the function call node from the tree,
    replacing it by the wrapped expression inside the parent.

    :param node: An astroid node.
    :type node:  astroid.bases.NodeNG
    :yields: The sequence of wrapped expressions on the modified tree
    expression can be found.
    """
    if (isinstance(node, nodes.Call)
            and isinstance(node.func, nodes.Name)
            and node.func.name == _TRANSIENT_FUNCTION):
        real_expr = node.args[0]
        real_expr.parent = node.parent
        # Search for node in all _astng_fields (the fields checked when
        # get_children is called) of its parent. Some of those fields may
        # be lists or tuples, in which case the elements need to be checked.
        # When we find it, replace it by real_expr, so that the AST looks
        # like no call to _TRANSIENT_FUNCTION ever took place.
        for name in node.parent._astroid_fields:
            child = getattr(node.parent, name)
            if isinstance(child, (list, tuple)):
                for idx, compound_child in enumerate(child):
                    if compound_child is node:
                        child[idx] = real_expr
            elif child is node:
                setattr(node.parent, name, real_expr)
        yield real_expr
    else:
        for child in node.get_children():
            for result in _extract_expressions(child):
                yield result


def _find_statement_by_line(node, line):
    """Extracts the statement on a specific line from an AST.

    If the line number of node matches line, it will be returned;
    otherwise its children are iterated and the function is called
    recursively.

    :param node: An astroid node.
    :type node: astroid.bases.NodeNG
    :param line: The line number of the statement to extract.
    :type line: int
    :returns: The statement on the line, or None if no statement for the line
      can be found.
    :rtype:  astroid.bases.NodeNG or None
    """
    if isinstance(node, (nodes.ClassDef, nodes.FunctionDef)):
        # This is an inaccuracy in the AST: the nodes that can be
        # decorated do not carry explicit information on which line
        # the actual definition (class/def), but .fromline seems to
        # be close enough.
        node_line = node.fromlineno
    else:
        node_line = node.lineno

    if node_line == line:
        return node

    for child in node.get_children():
        result = _find_statement_by_line(child, line)
        if result:
            return result

    return None

def extract_node(code, module_name=''):
    """Parses some Python code as a module and extracts a designated AST node.

    Statements:
     To extract one or more statement nodes, append #@ to the end of the line

     Examples:
       >>> def x():
       >>>   def y():
       >>>     return 1 #@

       The return statement will be extracted.

       >>> class X(object):
       >>>   def meth(self): #@
       >>>     pass

      The funcion object 'meth' will be extracted.

    Expressions:
     To extract arbitrary expressions, surround them with the fake
     function call __(...). After parsing, the surrounded expression
     will be returned and the whole AST (accessible via the returned
     node's parent attribute) will look like the function call was
     never there in the first place.

     Examples:
       >>> a = __(1)

       The const node will be extracted.

       >>> def x(d=__(foo.bar)): pass

       The node containing the default argument will be extracted.

       >>> def foo(a, b):
       >>>   return 0 < __(len(a)) < b

       The node containing the function call 'len' will be extracted.

    If no statements or expressions are selected, the last toplevel
    statement will be returned.

    If the selected statement is a discard statement, (i.e. an expression
    turned into a statement), the wrapped expression is returned instead.

    For convenience, singleton lists are unpacked.

    :param str code: A piece of Python code that is parsed as
    a module. Will be passed through textwrap.dedent first.
    :param str module_name: The name of the module.
    :returns: The designated node from the parse tree, or a list of nodes.
    :rtype: astroid.bases.NodeNG, or a list of nodes.
    """
    def _extract(node):
        if isinstance(node, nodes.Expr):
            return node.value
        else:
            return node

    requested_lines = []
    for idx, line in enumerate(code.splitlines()):
        if line.strip().endswith(_STATEMENT_SELECTOR):
            requested_lines.append(idx + 1)

    tree = builder.parse(code, module_name=module_name)
    extracted = []
    if requested_lines:
        for line in requested_lines:
            extracted.append(_find_statement_by_line(tree, line))

    # Modifies the tree.
    extracted.extend(_extract_expressions(tree))

    if not extracted:
        extracted.append(tree.body[-1])

    extracted = [_extract(node) for node in extracted]
    if len(extracted) == 1:
        return extracted[0]
    else:
        return extracted


def require_version(minver=None, maxver=None):
    """ Compare version of python interpreter to the given one. Skip the test
    if older.
    """
    def parse(string, default=None):
        string = string or default
        try:
            return tuple(int(v) for v in string.split('.'))
        except ValueError:
            raise ValueError('%s is not a correct version : should be X.Y[.Z].' % version)

    def check_require_version(f):
        current = sys.version_info[:3]
        if parse(minver, "0") < current <= parse(maxver, "4"):
            return f
        else:
            str_version = '.'.join(str(v) for v in sys.version_info)
            @functools.wraps(f)
            def new_f(self, *args, **kwargs):
                if minver is not None:
                    self.skipTest('Needs Python > %s. Current version is %s.' % (minver, str_version))
                elif maxver is not None:
                    self.skipTest('Needs Python <= %s. Current version is %s.' % (maxver, str_version))
            return new_f


    return check_require_version

def get_name_node(start_from, name, index=0):
    return [n for n in start_from.nodes_of_class(nodes.Name) if n.name == name][index]
