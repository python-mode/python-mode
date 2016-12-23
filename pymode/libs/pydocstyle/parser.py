"""Python code parser."""

import logging
import sys
import textwrap
import tokenize as tk
from collections import defaultdict
from itertools import chain, dropwhile
from re import compile as re

try:
    from StringIO import StringIO
except ImportError:  # Python 3.0 and later
    from io import StringIO

try:
    next
except NameError:  # Python 2.5 and earlier
    nothing = object()

    def next(obj, default=nothing):
        if default == nothing:
            return obj.next()
        else:
            try:
                return obj.next()
            except StopIteration:
                return default


__all__ = ('Parser', 'Definition', 'Module', 'Package', 'Function',
           'NestedFunction', 'Method', 'Class', 'NestedClass', 'AllError',
           'StringIO')


def humanize(string):
    return re(r'(.)([A-Z]+)').sub(r'\1 \2', string).lower()


class Value(object):
    """A generic object with a list of preset fields."""

    def __init__(self, *args):
        if len(self._fields) != len(args):
            raise ValueError('got {0} arguments for {1} fields for {2}: {3}'
                             .format(len(args), len(self._fields),
                                     self.__class__.__name__, self._fields))
        vars(self).update(zip(self._fields, args))

    def __hash__(self):
        return hash(repr(self))

    def __eq__(self, other):
        return other and vars(self) == vars(other)

    def __repr__(self):
        kwargs = ', '.join('{0}={1!r}'.format(field, getattr(self, field))
                           for field in self._fields)
        return '{0}({1})'.format(self.__class__.__name__, kwargs)


class Definition(Value):
    """A Python source code definition (could be class, function, etc)."""

    _fields = ('name', '_source', 'start', 'end', 'decorators', 'docstring',
               'children', 'parent', 'skipped_error_codes')

    _human = property(lambda self: humanize(type(self).__name__))
    kind = property(lambda self: self._human.split()[-1])
    module = property(lambda self: self.parent.module)
    all = property(lambda self: self.module.all)
    _slice = property(lambda self: slice(self.start - 1, self.end))
    is_class = False

    def __iter__(self):
        return chain([self], *self.children)

    @property
    def _publicity(self):
        return {True: 'public', False: 'private'}[self.is_public]

    @property
    def source(self):
        """Return the source code for the definition."""
        full_src = self._source[self._slice]

        def is_empty_or_comment(line):
            return line.strip() == '' or line.strip().startswith('#')

        filtered_src = dropwhile(is_empty_or_comment, reversed(full_src))
        return ''.join(reversed(list(filtered_src)))

    def __str__(self):
        out = 'in {0} {1} `{2}`'.format(self._publicity, self._human,
                                        self.name)
        if self.skipped_error_codes:
            out += ' (skipping {0})'.format(self.skipped_error_codes)
        return out


class Module(Definition):
    """A Python source code module."""

    _fields = ('name', '_source', 'start', 'end', 'decorators', 'docstring',
               'children', 'parent', '_all', 'future_imports',
               'skipped_error_codes')
    is_public = True
    _nest = staticmethod(lambda s: {'def': Function, 'class': Class}[s])
    module = property(lambda self: self)
    all = property(lambda self: self._all)

    def __str__(self):
        return 'at module level'


class Package(Module):
    """A package is a __init__.py module."""


class Function(Definition):
    """A Python source code function."""

    _nest = staticmethod(lambda s: {'def': NestedFunction,
                                    'class': NestedClass}[s])

    @property
    def is_public(self):
        """Return True iff this function should be considered public."""
        if self.all is not None:
            return self.name in self.all
        else:
            return not self.name.startswith('_')


class NestedFunction(Function):
    """A Python source code nested function."""

    is_public = False


class Method(Function):
    """A Python source code method."""

    @property
    def is_magic(self):
        """Return True iff this method is a magic method (e.g., `__str__`)."""
        return (self.name.startswith('__') and
                self.name.endswith('__') and
                self.name not in VARIADIC_MAGIC_METHODS)

    @property
    def is_public(self):
        """Return True iff this method should be considered public."""
        # Check if we are a setter/deleter method, and mark as private if so.
        for decorator in self.decorators:
            # Given 'foo', match 'foo.bar' but not 'foobar' or 'sfoo'
            if re(r"^{0}\.".format(self.name)).match(decorator.name):
                return False
        name_is_public = (not self.name.startswith('_') or
                          self.name in VARIADIC_MAGIC_METHODS or
                          self.is_magic)
        return self.parent.is_public and name_is_public


class Class(Definition):
    """A Python source code class."""

    _nest = staticmethod(lambda s: {'def': Method, 'class': NestedClass}[s])
    is_public = Function.is_public
    is_class = True


class NestedClass(Class):
    """A Python source code nested class."""

    @property
    def is_public(self):
        """Return True iff this class should be considered public."""
        return (not self.name.startswith('_') and
                self.parent.is_class and
                self.parent.is_public)


class Decorator(Value):
    """A decorator for function, method or class."""

    _fields = 'name arguments'.split()


VARIADIC_MAGIC_METHODS = ('__init__', '__call__', '__new__')


class AllError(Exception):
    """Raised when there is a problem with __all__ when parsing."""

    def __init__(self, message):
        """Initialize the error with a more specific message."""
        Exception.__init__(
            self, message + textwrap.dedent("""
                That means pydocstyle cannot decide which definitions are
                public. Variable __all__ should be present at most once in
                each file, in form
                `__all__ = ('a_public_function', 'APublicClass', ...)`.
                More info on __all__: http://stackoverflow.com/q/44834/. ')
                """))


class TokenStream(object):
    def __init__(self, filelike):
        self._generator = tk.generate_tokens(filelike.readline)
        self.current = Token(*next(self._generator, None))
        self.line = self.current.start[0]

    def move(self):
        previous = self.current
        current = next(self._generator, None)
        self.current = None if current is None else Token(*current)
        self.line = self.current.start[0] if self.current else self.line
        return previous

    def __iter__(self):
        while True:
            if self.current is not None:
                yield self.current
            else:
                return
            self.move()


class TokenKind(int):
    def __repr__(self):
        return "tk.{0}".format(tk.tok_name[self])


class Token(Value):
    _fields = 'kind value start end source'.split()

    def __init__(self, *args):
        super(Token, self).__init__(*args)
        self.kind = TokenKind(self.kind)


class Parser(object):
    """A Python source code parser."""

    def parse(self, filelike, filename):
        """Parse the given file-like object and return its Module object."""
        # TODO: fix log
        self.log = logging.getLogger()
        self.source = filelike.readlines()
        src = ''.join(self.source)
        self.stream = TokenStream(StringIO(src))
        self.filename = filename
        self.all = None
        self.future_imports = defaultdict(lambda: False)
        self._accumulated_decorators = []
        return self.parse_module()

    # TODO: remove
    def __call__(self, *args, **kwargs):
        """Call the parse method."""
        return self.parse(*args, **kwargs)

    current = property(lambda self: self.stream.current)
    line = property(lambda self: self.stream.line)

    def consume(self, kind):
        """Consume one token and verify it is of the expected kind."""
        next_token = self.stream.move()
        assert next_token.kind == kind

    def leapfrog(self, kind, value=None):
        """Skip tokens in the stream until a certain token kind is reached.

        If `value` is specified, tokens whose values are different will also
        be skipped.
        """
        while self.current is not None:
            if (self.current.kind == kind and
                    (value is None or self.current.value == value)):
                self.consume(kind)
                return
            self.stream.move()

    def parse_docstring(self):
        """Parse a single docstring and return its value."""
        self.log.debug("parsing docstring, token is %r (%s)",
                       self.current.kind, self.current.value)
        while self.current.kind in (tk.COMMENT, tk.NEWLINE, tk.NL):
            self.stream.move()
            self.log.debug("parsing docstring, token is %r (%s)",
                           self.current.kind, self.current.value)
        if self.current.kind == tk.STRING:
            docstring = self.current.value
            self.stream.move()
            return docstring
        return None

    def parse_decorators(self):
        """Called after first @ is found.

        Parse decorators into self._accumulated_decorators.
        Continue to do so until encountering the 'def' or 'class' start token.
        """
        name = []
        arguments = []
        at_arguments = False

        while self.current is not None:
            if (self.current.kind == tk.NAME and
                    self.current.value in ['def', 'class']):
                # Done with decorators - found function or class proper
                break
            elif self.current.kind == tk.OP and self.current.value == '@':
                # New decorator found. Store the decorator accumulated so far:
                self._accumulated_decorators.append(
                    Decorator(''.join(name), ''.join(arguments)))
                # Now reset to begin accumulating the new decorator:
                name = []
                arguments = []
                at_arguments = False
            elif self.current.kind == tk.OP and self.current.value == '(':
                at_arguments = True
            elif self.current.kind == tk.OP and self.current.value == ')':
                # Ignore close parenthesis
                pass
            elif self.current.kind == tk.NEWLINE or self.current.kind == tk.NL:
                # Ignore newlines
                pass
            else:
                # Keep accumulating current decorator's name or argument.
                if not at_arguments:
                    name.append(self.current.value)
                else:
                    arguments.append(self.current.value)
            self.stream.move()

        # Add decorator accumulated so far
        self._accumulated_decorators.append(
            Decorator(''.join(name), ''.join(arguments)))

    def parse_definitions(self, class_, all=False):
        """Parse multiple definitions and yield them."""
        while self.current is not None:
            self.log.debug("parsing definition list, current token is %r (%s)",
                           self.current.kind, self.current.value)
            if all and self.current.value == '__all__':
                self.parse_all()
            elif self.current.kind == tk.OP and self.current.value == '@':
                self.consume(tk.OP)
                self.parse_decorators()
            elif self.current.value in ['def', 'class']:
                yield self.parse_definition(class_._nest(self.current.value))
            elif self.current.kind == tk.INDENT:
                self.consume(tk.INDENT)
                for definition in self.parse_definitions(class_):
                    yield definition
            elif self.current.kind == tk.DEDENT:
                self.consume(tk.DEDENT)
                return
            elif self.current.value == 'from':
                self.parse_from_import_statement()
            else:
                self.stream.move()

    def parse_all(self):
        """Parse the __all__ definition in a module."""
        assert self.current.value == '__all__'
        self.consume(tk.NAME)
        if self.current.value != '=':
            raise AllError('Could not evaluate contents of __all__. ')
        self.consume(tk.OP)
        if self.current.value not in '([':
            raise AllError('Could not evaluate contents of __all__. ')
        if self.current.value == '[':
            sys.stderr.write(
                "{0} WARNING: __all__ is defined as a list, this means "
                "pydocstyle cannot reliably detect contents of the __all__ "
                "variable, because it can be mutated. Change __all__ to be "
                "an (immutable) tuple, to remove this warning. Note, "
                "pydocstyle uses __all__ to detect which definitions are "
                "public, to warn if public definitions are missing "
                "docstrings. If __all__ is a (mutable) list, pydocstyle "
                "cannot reliably assume its contents. pydocstyle will "
                "proceed assuming __all__ is not mutated.\n"
                .format(self.filename))
        self.consume(tk.OP)

        self.all = []
        all_content = "("
        while self.current.kind != tk.OP or self.current.value not in ")]":
            if self.current.kind in (tk.NL, tk.COMMENT):
                pass
            elif (self.current.kind == tk.STRING or
                    self.current.value == ','):
                all_content += self.current.value
            else:
                raise AllError('Unexpected token kind in  __all__: {0!r}. '
                               .format(self.current.kind))
            self.stream.move()
        self.consume(tk.OP)
        all_content += ")"
        try:
            self.all = eval(all_content, {})
        except BaseException as e:
            raise AllError('Could not evaluate contents of __all__.'
                           '\bThe value was {0}. The exception was:\n{1}'
                           .format(all_content, e))

    def parse_module(self):
        """Parse a module (and its children) and return a Module object."""
        self.log.debug("parsing module.")
        start = self.line
        docstring = self.parse_docstring()
        children = list(self.parse_definitions(Module, all=True))
        assert self.current is None, self.current
        end = self.line
        cls = Module
        if self.filename.endswith('__init__.py'):
            cls = Package
        module = cls(self.filename, self.source, start, end,
                     [], docstring, children, None, self.all, None, '')
        for child in module.children:
            child.parent = module
        module.future_imports = self.future_imports
        self.log.debug("finished parsing module.")
        return module

    def parse_definition(self, class_):
        """Parse a definition and return its value in a `class_` object."""
        start = self.line
        self.consume(tk.NAME)
        name = self.current.value
        self.log.debug("parsing %s '%s'", class_.__name__, name)
        self.stream.move()
        if self.current.kind == tk.OP and self.current.value == '(':
            parenthesis_level = 0
            while True:
                if self.current.kind == tk.OP:
                    if self.current.value == '(':
                        parenthesis_level += 1
                    elif self.current.value == ')':
                        parenthesis_level -= 1
                        if parenthesis_level == 0:
                            break
                self.stream.move()
        if self.current.kind != tk.OP or self.current.value != ':':
            self.leapfrog(tk.OP, value=":")
        else:
            self.consume(tk.OP)
        if self.current.kind in (tk.NEWLINE, tk.COMMENT):
            skipped_error_codes = self.parse_skip_comment()
            self.leapfrog(tk.INDENT)
            assert self.current.kind != tk.INDENT
            docstring = self.parse_docstring()
            decorators = self._accumulated_decorators
            self._accumulated_decorators = []
            self.log.debug("parsing nested definitions.")
            children = list(self.parse_definitions(class_))
            self.log.debug("finished parsing nested definitions for '%s'",
                           name)
            end = self.line - 1
        else:  # one-liner definition
            skipped_error_codes = ''
            docstring = self.parse_docstring()
            decorators = []  # TODO
            children = []
            end = self.line
            self.leapfrog(tk.NEWLINE)
        definition = class_(name, self.source, start, end,
                            decorators, docstring, children, None,
                            skipped_error_codes)
        for child in definition.children:
            child.parent = definition
        self.log.debug("finished parsing %s '%s'. Next token is %r (%s)",
                       class_.__name__, name, self.current.kind,
                       self.current.value)
        return definition

    def parse_skip_comment(self):
        """Parse a definition comment for noqa skips."""
        skipped_error_codes = ''
        if self.current.kind == tk.COMMENT:
            if 'noqa: ' in self.current.value:
                skipped_error_codes = ''.join(
                     self.current.value.split('noqa: ')[1:])
            elif self.current.value.startswith('# noqa'):
                skipped_error_codes = 'all'
        return skipped_error_codes

    def check_current(self, kind=None, value=None):
        """Verify the current token is of type `kind` and equals `value`."""
        msg = textwrap.dedent("""
        Unexpected token at line {self.line}:

        In file: {self.filename}

        Got kind {self.current.kind!r}
        Got value {self.current.value}
        """.format(self=self))
        kind_valid = self.current.kind == kind if kind else True
        value_valid = self.current.value == value if value else True
        assert kind_valid and value_valid, msg

    def parse_from_import_statement(self):
        """Parse a 'from x import y' statement.

        The purpose is to find __future__ statements.

        """
        self.log.debug('parsing from/import statement.')
        is_future_import = self._parse_from_import_source()
        self._parse_from_import_names(is_future_import)

    def _parse_from_import_source(self):
        """Parse the 'from x import' part in a 'from x import y' statement.

        Return true iff `x` is __future__.
        """
        assert self.current.value == 'from', self.current.value
        self.stream.move()
        is_future_import = self.current.value == '__future__'
        self.stream.move()
        while (self.current is not None and
               self.current.kind in (tk.DOT, tk.NAME, tk.OP) and
               self.current.value != 'import'):
            self.stream.move()
        if self.current is None or self.current.value != 'import':
            return False
        self.check_current(value='import')
        assert self.current.value == 'import', self.current.value
        self.stream.move()
        return is_future_import

    def _parse_from_import_names(self, is_future_import):
        """Parse the 'y' part in a 'from x import y' statement."""
        if self.current.value == '(':
            self.consume(tk.OP)
            expected_end_kinds = (tk.OP, )
        else:
            expected_end_kinds = (tk.NEWLINE, tk.ENDMARKER)
        while self.current.kind not in expected_end_kinds and not (
                    self.current.kind == tk.OP and self.current.value == ';'):
            if self.current.kind != tk.NAME:
                self.stream.move()
                continue
            self.log.debug("parsing import, token is %r (%s)",
                           self.current.kind, self.current.value)
            if is_future_import:
                self.log.debug('found future import: %s', self.current.value)
                self.future_imports[self.current.value] = True
            self.consume(tk.NAME)
            self.log.debug("parsing import, token is %r (%s)",
                           self.current.kind, self.current.value)
            if self.current.kind == tk.NAME and self.current.value == 'as':
                self.consume(tk.NAME)  # as
                if self.current.kind == tk.NAME:
                    self.consume(tk.NAME)  # new name, irrelevant
            if self.current.value == ',':
                self.consume(tk.OP)
            self.log.debug("parsing import, token is %r (%s)",
                           self.current.kind, self.current.value)
