""" Meager code path measurement tool.
    Ned Batchelder
    http://nedbatchelder.com/blog/200803/python_code_complexity_microtool.html
    MIT License.
"""
from __future__ import with_statement

import optparse
import sys
from collections import defaultdict
try:
    import ast
    from ast import iter_child_nodes
except ImportError:   # Python 2.5
    from flake8.util import ast, iter_child_nodes

__version__ = '0.2.1'


class ASTVisitor(object):
    """Performs a depth-first walk of the AST."""

    def __init__(self):
        self.node = None
        self._cache = {}

    def default(self, node, *args):
        for child in iter_child_nodes(node):
            self.dispatch(child, *args)

    def dispatch(self, node, *args):
        self.node = node
        klass = node.__class__
        meth = self._cache.get(klass)
        if meth is None:
            className = klass.__name__
            meth = getattr(self.visitor, 'visit' + className, self.default)
            self._cache[klass] = meth
        return meth(node, *args)

    def preorder(self, tree, visitor, *args):
        """Do preorder walk of tree using visitor"""
        self.visitor = visitor
        visitor.visit = self.dispatch
        self.dispatch(tree, *args)  # XXX *args make sense?


class PathNode(object):
    def __init__(self, name, look="circle"):
        self.name = name
        self.look = look

    def to_dot(self):
        print('node [shape=%s,label="%s"] %d;' % (
            self.look, self.name, self.dot_id()))

    def dot_id(self):
        return id(self)


class PathGraph(object):
    def __init__(self, name, entity, lineno):
        self.name = name
        self.entity = entity
        self.lineno = lineno
        self.nodes = defaultdict(list)

    def connect(self, n1, n2):
        self.nodes[n1].append(n2)

    def to_dot(self):
        print('subgraph {')
        for node in self.nodes:
            node.to_dot()
        for node, nexts in self.nodes.items():
            for next in nexts:
                print('%s -- %s;' % (node.dot_id(), next.dot_id()))
        print('}')

    def complexity(self):
        """ Return the McCabe complexity for the graph.
            V-E+2
        """
        num_edges = sum([len(n) for n in self.nodes.values()])
        num_nodes = len(self.nodes)
        return num_edges - num_nodes + 2


class PathGraphingAstVisitor(ASTVisitor):
    """ A visitor for a parsed Abstract Syntax Tree which finds executable
        statements.
    """

    def __init__(self):
        super(PathGraphingAstVisitor, self).__init__()
        self.classname = ""
        self.graphs = {}
        self.reset()

    def reset(self):
        self.graph = None
        self.tail = None

    def dispatch_list(self, node_list):
        for node in node_list:
            self.dispatch(node)

    def visitFunctionDef(self, node):

        if self.classname:
            entity = '%s%s' % (self.classname, node.name)
        else:
            entity = node.name

        name = '%d:1: %r' % (node.lineno, entity)

        if self.graph is not None:
            # closure
            pathnode = self.appendPathNode(name)
            self.tail = pathnode
            self.dispatch_list(node.body)
            bottom = PathNode("", look='point')
            self.graph.connect(self.tail, bottom)
            self.graph.connect(pathnode, bottom)
            self.tail = bottom
        else:
            self.graph = PathGraph(name, entity, node.lineno)
            pathnode = PathNode(name)
            self.tail = pathnode
            self.dispatch_list(node.body)
            self.graphs["%s%s" % (self.classname, node.name)] = self.graph
            self.reset()

    def visitClassDef(self, node):
        old_classname = self.classname
        self.classname += node.name + "."
        self.dispatch_list(node.body)
        self.classname = old_classname

    def appendPathNode(self, name):
        if not self.tail:
            return
        pathnode = PathNode(name)
        self.graph.connect(self.tail, pathnode)
        self.tail = pathnode
        return pathnode

    def visitSimpleStatement(self, node):
        if node.lineno is None:
            lineno = 0
        else:
            lineno = node.lineno
        name = "Stmt %d" % lineno
        self.appendPathNode(name)

    visitAssert = visitAssign = visitAugAssign = visitDelete = visitPrint = \
        visitRaise = visitYield = visitImport = visitCall = visitSubscript = \
        visitPass = visitContinue = visitBreak = visitGlobal = visitReturn = \
        visitSimpleStatement

    def visitLoop(self, node):
        name = "Loop %d" % node.lineno

        if self.graph is None:
            # global loop
            self.graph = PathGraph(name, name, node.lineno)
            pathnode = PathNode(name)
            self.tail = pathnode
            self.dispatch_list(node.body)
            self.graphs["%s%s" % (self.classname, name)] = self.graph
            self.reset()
        else:
            pathnode = self.appendPathNode(name)
            self.tail = pathnode
            self.dispatch_list(node.body)
            bottom = PathNode("", look='point')
            self.graph.connect(self.tail, bottom)
            self.graph.connect(pathnode, bottom)
            self.tail = bottom

        # TODO: else clause in node.orelse

    visitFor = visitWhile = visitLoop

    def visitIf(self, node):
        name = "If %d" % node.lineno
        pathnode = self.appendPathNode(name)
        loose_ends = []
        self.dispatch_list(node.body)
        loose_ends.append(self.tail)
        if node.orelse:
            self.tail = pathnode
            self.dispatch_list(node.orelse)
            loose_ends.append(self.tail)
        else:
            loose_ends.append(pathnode)
        if pathnode:
            bottom = PathNode("", look='point')
            for le in loose_ends:
                self.graph.connect(le, bottom)
            self.tail = bottom

    def visitTryExcept(self, node):
        name = "TryExcept %d" % node.lineno
        pathnode = self.appendPathNode(name)
        loose_ends = []
        self.dispatch_list(node.body)
        loose_ends.append(self.tail)
        for handler in node.handlers:
            self.tail = pathnode
            self.dispatch_list(handler.body)
            loose_ends.append(self.tail)
        if pathnode:
            bottom = PathNode("", look='point')
            for le in loose_ends:
                self.graph.connect(le, bottom)
            self.tail = bottom

    def visitWith(self, node):
        name = "With %d" % node.lineno
        self.appendPathNode(name)
        self.dispatch_list(node.body)


class McCabeChecker(object):
    """McCabe cyclomatic complexity checker."""
    name = 'mccabe'
    version = __version__
    _code = 'C901'
    _error_tmpl = "C901 %r is too complex (%d)"
    max_complexity = 0

    def __init__(self, tree, filename):
        self.tree = tree

    @classmethod
    def add_options(cls, parser):
        parser.add_option('--max-complexity', default=-1, action='store',
                          type='int', help="McCabe complexity threshold")
        parser.config_options.append('max-complexity')

    @classmethod
    def parse_options(cls, options):
        cls.max_complexity = options.max_complexity

    def run(self):
        if self.max_complexity < 0:
            return
        visitor = PathGraphingAstVisitor()
        visitor.preorder(self.tree, visitor)
        for graph in visitor.graphs.values():
            if graph.complexity() >= self.max_complexity:
                text = self._error_tmpl % (graph.entity, graph.complexity())
                yield graph.lineno, 0, text, type(self)


def get_code_complexity(code, threshold=7, filename='stdin'):
    try:
        tree = compile(code, filename, "exec", ast.PyCF_ONLY_AST)
    except SyntaxError:
        e = sys.exc_info()[1]
        sys.stderr.write("Unable to parse %s: %s\n" % (filename, e))
        return 0

    complx = []
    McCabeChecker.max_complexity = threshold
    for lineno, offset, text, check in McCabeChecker(tree, filename).run():
        complx.append('%s:%d:1: %s' % (filename, lineno, text))

    if len(complx) == 0:
        return 0
    print('\n'.join(complx))
    return len(complx)


def get_module_complexity(module_path, threshold=7):
    """Returns the complexity of a module"""
    with open(module_path, "rU") as mod:
        code = mod.read()
    return get_code_complexity(code, threshold, filename=module_path)


def main(argv):
    opar = optparse.OptionParser()
    opar.add_option("-d", "--dot", dest="dot",
                    help="output a graphviz dot file", action="store_true")
    opar.add_option("-m", "--min", dest="threshold",
                    help="minimum complexity for output", type="int",
                    default=2)

    options, args = opar.parse_args(argv)

    with open(args[0], "rU") as mod:
        code = mod.read()
    tree = compile(code, args[0], "exec", ast.PyCF_ONLY_AST)
    visitor = PathGraphingAstVisitor()
    visitor.preorder(tree, visitor)

    if options.dot:
        print('graph {')
        for graph in visitor.graphs.values():
            if graph.complexity() >= options.threshold:
                graph.to_dot()
        print('}')
    else:
        for graph in visitor.graphs.values():
            if graph.complexity() >= options.threshold:
                print(graph.name, graph.complexity())


if __name__ == '__main__':
    main(sys.argv[1:])
