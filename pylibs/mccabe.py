""" Meager code path measurement tool.
    Ned Batchelder
    http://nedbatchelder.com/blog/200803/python_code_complexity_microtool.html
    MIT License.
"""
try:
    from compiler import parse      # NOQA
    iter_child_nodes = None         # NOQA
except ImportError:
    from ast import parse, iter_child_nodes     # NOQA

import optparse
import sys
from collections import defaultdict

WARNING_CODE = "W901"


class ASTVisitor:

    VERBOSE = 0

    def __init__(self):
        self.node = None
        self._cache = {}

    def default(self, node, *args):
        if hasattr(node, 'getChildNodes'):
            children = node.getChildNodes()
        else:
            children = iter_child_nodes(node)

        for child in children:
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


class PathNode:
    def __init__(self, name, look="circle"):
        self.name = name
        self.look = look

    def to_dot(self):
        print('node [shape=%s,label="%s"] %d;' % \
                (self.look, self.name, self.dot_id()))

    def dot_id(self):
        return id(self)


class PathGraph:
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
        ASTVisitor.__init__(self)
        self.classname = ""
        self.graphs = {}
        self.reset()

    def reset(self):
        self.graph = None
        self.tail = None

    def visitFunction(self, node):

        if self.classname:
            entity = '%s%s' % (self.classname, node.name)
        else:
            entity = node.name

        name = '%d:1: %r' % (node.lineno, entity)

        if self.graph is not None:
            # closure
            pathnode = self.appendPathNode(name)
            self.tail = pathnode
            self.default(node)
            bottom = PathNode("", look='point')
            self.graph.connect(self.tail, bottom)
            self.graph.connect(pathnode, bottom)
            self.tail = bottom
        else:
            self.graph = PathGraph(name, entity, node.lineno)
            pathnode = PathNode(name)
            self.tail = pathnode
            self.default(node)
            self.graphs["%s%s" % (self.classname, node.name)] = self.graph
            self.reset()

    visitFunctionDef = visitFunction

    def visitClass(self, node):
        old_classname = self.classname
        self.classname += node.name + "."
        self.default(node)
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

    visitAssert = visitAssign = visitAssTuple = visitPrint = \
        visitPrintnl = visitRaise = visitSubscript = visitDecorators = \
        visitPass = visitDiscard = visitGlobal = visitReturn = \
        visitSimpleStatement

    def visitLoop(self, node):
        name = "Loop %d" % node.lineno

        if self.graph is None:
            # global loop
            self.graph = PathGraph(name, name, node.lineno)
            pathnode = PathNode(name)
            self.tail = pathnode
            self.default(node)
            self.graphs["%s%s" % (self.classname, name)] = self.graph
            self.reset()
        else:
            pathnode = self.appendPathNode(name)
            self.tail = pathnode
            self.default(node.body)
            bottom = PathNode("", look='point')
            self.graph.connect(self.tail, bottom)
            self.graph.connect(pathnode, bottom)
            self.tail = bottom

        # TODO: else clause in node.else_

    visitFor = visitWhile = visitLoop

    def visitIf(self, node):
        name = "If %d" % node.lineno
        pathnode = self.appendPathNode(name)
        if not pathnode:
            return  # TODO: figure out what to do with if's outside def's.
        loose_ends = []
        for t, n in node.tests:
            self.tail = pathnode
            self.default(n)
            loose_ends.append(self.tail)
        if node.else_:
            self.tail = pathnode
            self.default(node.else_)
            loose_ends.append(self.tail)
        else:
            loose_ends.append(pathnode)
        bottom = PathNode("", look='point')
        for le in loose_ends:
            self.graph.connect(le, bottom)
        self.tail = bottom

    # TODO: visitTryExcept
    # TODO: visitTryFinally
    # TODO: visitWith

    # XXX todo: determine which ones can add to the complexity
    # py2
    # TODO: visitStmt
    # TODO: visitAssName
    # TODO: visitCallFunc
    # TODO: visitConst

    # py3
    # TODO: visitStore
    # TODO: visitCall
    # TODO: visitLoad
    # TODO: visitNum
    # TODO: visitarguments
    # TODO: visitExpr


def get_code_complexity(code, min=7, filename='stdin'):
    complex = []
    try:
        ast = parse(code)
    except AttributeError:
        e = sys.exc_info()[1]
        sys.stderr.write("Unable to parse %s: %s\n" % (filename, e))
        return 0

    visitor = PathGraphingAstVisitor()
    visitor.preorder(ast, visitor)
    for graph in visitor.graphs.values():
        if graph is None:
            # ?
            continue
        if graph.complexity() >= min:
            complex.append(dict(
                type = 'W',
                lnum = graph.lineno,
                text = '%s %r is too complex (%d)' % (
                    WARNING_CODE,
                    graph.entity,
                    graph.complexity(),
                )
            ))

    return complex


def get_module_complexity(module_path, min=7):
    """Returns the complexity of a module"""
    code = open(module_path, "rU").read() + '\n\n'
    return get_code_complexity(code, min, filename=module_path)


def main(argv):
    opar = optparse.OptionParser()
    opar.add_option("-d", "--dot", dest="dot",
                    help="output a graphviz dot file", action="store_true")
    opar.add_option("-m", "--min", dest="min",
                    help="minimum complexity for output", type="int",
                    default=2)

    options, args = opar.parse_args(argv)

    text = open(args[0], "rU").read() + '\n\n'
    ast = parse(text)
    visitor = PathGraphingAstVisitor()
    visitor.preorder(ast, visitor)

    if options.dot:
        print('graph {')
        for graph in visitor.graphs.values():
            if graph.complexity() >= options.min:
                graph.to_dot()
        print('}')
    else:
        for graph in visitor.graphs.values():
            if graph.complexity() >= options.min:
                print(graph.name, graph.complexity())


if __name__ == '__main__':
    main(sys.argv[1:])
