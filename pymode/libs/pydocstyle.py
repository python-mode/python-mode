#! /usr/bin/env python
"""Static analysis tool for checking docstring conventions and style.

The repository is located at:
http://github.com/PyCQA/pydocstyle

"""
from __future__ import with_statement

import os
import string
import sys
import ast
import copy
import logging
import textwrap
import tokenize as tk
from itertools import takewhile, dropwhile, chain
from re import compile as re
import itertools
from collections import defaultdict, namedtuple, Set

try:  # Python 3.x
    from ConfigParser import RawConfigParser
except ImportError:  # Python 2.x
    from configparser import RawConfigParser

log = logging.getLogger(__name__)


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


# If possible (python >= 3.2) use tokenize.open to open files, so PEP 263
# encoding markers are interpreted.
try:
    tokenize_open = tk.open
except AttributeError:
    tokenize_open = open


__version__ = '1.1.0'
__all__ = ('check',)


class ReturnCode(object):
    no_violations_found = 0
    violations_found = 1
    invalid_options = 2


VARIADIC_MAGIC_METHODS = ('__init__', '__call__', '__new__')


def humanize(string):
    return re(r'(.)([A-Z]+)').sub(r'\1 \2', string).lower()


def is_magic(name):
    return (name.startswith('__') and
            name.endswith('__') and
            name not in VARIADIC_MAGIC_METHODS)


def is_ascii(string):
    return all(ord(char) < 128 for char in string)


def is_blank(string):
    return not string.strip()


def leading_space(string):
    return re('\s*').match(string).group()


class Value(object):

    def __init__(self, *args):
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

    _fields = ('name', '_source', 'start', 'end', 'decorators', 'docstring',
               'children', 'parent')

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
        return 'in %s %s `%s`' % (self._publicity, self._human, self.name)


class Module(Definition):

    _fields = ('name', '_source', 'start', 'end', 'decorators', 'docstring',
               'children', 'parent', '_all', 'future_imports')
    is_public = True
    _nest = staticmethod(lambda s: {'def': Function, 'class': Class}[s])
    module = property(lambda self: self)
    all = property(lambda self: self._all)

    def __str__(self):
        return 'at module level'


class Package(Module):
    """A package is a __init__.py module."""


class Function(Definition):

    _nest = staticmethod(lambda s: {'def': NestedFunction,
                                    'class': NestedClass}[s])

    @property
    def is_public(self):
        if self.all is not None:
            return self.name in self.all
        else:
            return not self.name.startswith('_')


class NestedFunction(Function):

    is_public = False


class Method(Function):

    @property
    def is_public(self):
        # Check if we are a setter/deleter method, and mark as private if so.
        for decorator in self.decorators:
            # Given 'foo', match 'foo.bar' but not 'foobar' or 'sfoo'
            if re(r"^{0}\.".format(self.name)).match(decorator.name):
                return False
        name_is_public = (not self.name.startswith('_') or
                          self.name in VARIADIC_MAGIC_METHODS or
                          is_magic(self.name))
        return self.parent.is_public and name_is_public


class Class(Definition):

    _nest = staticmethod(lambda s: {'def': Method, 'class': NestedClass}[s])
    is_public = Function.is_public
    is_class = True


class NestedClass(Class):

    @property
    def is_public(self):
        return (not self.name.startswith('_') and
                self.parent.is_class and
                self.parent.is_public)


class Decorator(Value):
    """A decorator for function, method or class."""

    _fields = 'name arguments'.split()


class TokenKind(int):
    def __repr__(self):
        return "tk.{0}".format(tk.tok_name[self])


class Token(Value):

    _fields = 'kind value start end source'.split()

    def __init__(self, *args):
        super(Token, self).__init__(*args)
        self.kind = TokenKind(self.kind)


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


class AllError(Exception):

    def __init__(self, message):
        Exception.__init__(
            self, message +
            'That means pydocstyle cannot decide which definitions are public.'
            ' Variable __all__ should be present at most once in each file, '
            "in form `__all__ = ('a_public_function', 'APublicClass', ...)`. "
            'More info on __all__: http://stackoverflow.com/q/44834/. ')


class Parser(object):

    def __call__(self, filelike, filename):
        self.source = filelike.readlines()
        src = ''.join(self.source)
        self.stream = TokenStream(StringIO(src))
        self.filename = filename
        self.all = None
        self.future_imports = defaultdict(lambda: False)
        self._accumulated_decorators = []
        return self.parse_module()

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
        log.debug("parsing docstring, token is %r (%s)",
                  self.current.kind, self.current.value)
        while self.current.kind in (tk.COMMENT, tk.NEWLINE, tk.NL):
            self.stream.move()
            log.debug("parsing docstring, token is %r (%s)",
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
            log.debug("parsing definition list, current token is %r (%s)",
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
            msg = ("%s WARNING: __all__ is defined as a list, this means "
                   "pydocstyle cannot reliably detect contents of the __all__ "
                   "variable, because it can be mutated. Change __all__ to be "
                   "an (immutable) tuple, to remove this warning. Note, "
                   "pydocstyle uses __all__ to detect which definitions are "
                   "public, to warn if public definitions are missing "
                   "docstrings. If __all__ is a (mutable) list, pydocstyle "
                   "cannot reliably assume its contents. pydocstyle will "
                   "proceed assuming __all__ is not mutated.\n"
                   % self.filename)
            sys.stderr.write(msg)
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
                raise AllError('Unexpected token kind in  __all__: %r. ' %
                               self.current.kind)
            self.stream.move()
        self.consume(tk.OP)
        all_content += ")"
        try:
            self.all = eval(all_content, {})
        except BaseException as e:
            raise AllError('Could not evaluate contents of __all__.'
                           '\bThe value was %s. The exception was:\n%s'
                           % (all_content, e))

    def parse_module(self):
        """Parse a module (and its children) and return a Module object."""
        log.debug("parsing module.")
        start = self.line
        docstring = self.parse_docstring()
        children = list(self.parse_definitions(Module, all=True))
        assert self.current is None, self.current
        end = self.line
        cls = Module
        if self.filename.endswith('__init__.py'):
            cls = Package
        module = cls(self.filename, self.source, start, end,
                     [], docstring, children, None, self.all)
        for child in module.children:
            child.parent = module
        module.future_imports = self.future_imports
        log.debug("finished parsing module.")
        return module

    def parse_definition(self, class_):
        """Parse a definition and return its value in a `class_` object."""
        start = self.line
        self.consume(tk.NAME)
        name = self.current.value
        log.debug("parsing %s '%s'", class_.__name__, name)
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
            self.leapfrog(tk.INDENT)
            assert self.current.kind != tk.INDENT
            docstring = self.parse_docstring()
            decorators = self._accumulated_decorators
            self._accumulated_decorators = []
            log.debug("parsing nested definitions.")
            children = list(self.parse_definitions(class_))
            log.debug("finished parsing nested definitions for '%s'", name)
            end = self.line - 1
        else:  # one-liner definition
            docstring = self.parse_docstring()
            decorators = []  # TODO
            children = []
            end = self.line
            self.leapfrog(tk.NEWLINE)
        definition = class_(name, self.source, start, end,
                            decorators, docstring, children, None)
        for child in definition.children:
            child.parent = definition
        log.debug("finished parsing %s '%s'. Next token is %r (%s)",
                  class_.__name__, name, self.current.kind,
                  self.current.value)
        return definition

    def check_current(self, kind=None, value=None):
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
        log.debug('parsing from/import statement.')
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
        while (self.current.kind in (tk.DOT, tk.NAME, tk.OP) and
               self.current.value != 'import'):
            self.stream.move()
        self.check_current(value='import')
        assert self.current.value == 'import', self.current.value
        self.stream.move()
        return is_future_import

    def _parse_from_import_names(self, is_future_import):
        """Parse the 'y' part in a 'from x import y' statement."""
        if self.current.value == '(':
            self.consume(tk.OP)
            expected_end_kind = tk.OP
        else:
            expected_end_kind = tk.NEWLINE
        while self.current.kind != expected_end_kind and not(
                self.current.kind == tk.OP and self.current.value == ';'):
            if self.current.kind != tk.NAME:
                self.stream.move()
                continue
            log.debug("parsing import, token is %r (%s)",
                      self.current.kind, self.current.value)
            if is_future_import:
                log.debug('found future import: %s', self.current.value)
                self.future_imports[self.current.value] = True
            self.consume(tk.NAME)
            log.debug("parsing import, token is %r (%s)",
                      self.current.kind, self.current.value)
            if self.current.kind == tk.NAME and self.current.value == 'as':
                self.consume(tk.NAME)  # as
                if self.current.kind == tk.NAME:
                    self.consume(tk.NAME)  # new name, irrelevant
            if self.current.value == ',':
                self.consume(tk.OP)
            log.debug("parsing import, token is %r (%s)",
                      self.current.kind, self.current.value)


class Error(object):
    """Error in docstring style."""

    # should be overridden by inheriting classes
    code = None
    short_desc = None
    context = None

    # Options that define how errors are printed:
    explain = False
    source = False

    def __init__(self, *parameters):
        self.parameters = parameters
        self.definition = None
        self.explanation = None

    def set_context(self, definition, explanation):
        self.definition = definition
        self.explanation = explanation

    filename = property(lambda self: self.definition.module.name)
    line = property(lambda self: self.definition.start)

    @property
    def message(self):
        ret = '%s: %s' % (self.code, self.short_desc)
        if self.context is not None:
            ret += ' (' + self.context % self.parameters + ')'
        return ret

    @property
    def lines(self):
        source = ''
        lines = self.definition._source[self.definition._slice]
        offset = self.definition.start
        lines_stripped = list(reversed(list(dropwhile(is_blank,
                                                      reversed(lines)))))
        numbers_width = 0
        for n, line in enumerate(lines_stripped):
            numbers_width = max(numbers_width, n + offset)
        numbers_width = len(str(numbers_width))
        numbers_width = 6
        for n, line in enumerate(lines_stripped):
            source += '%*d: %s' % (numbers_width, n + offset, line)
            if n > 5:
                source += '        ...\n'
                break
        return source

    def __str__(self):
        self.explanation = '\n'.join(l for l in self.explanation.split('\n')
                                     if not is_blank(l))
        template = '%(filename)s:%(line)s %(definition)s:\n        %(message)s'
        if self.source and self.explain:
            template += '\n\n%(explanation)s\n\n%(lines)s\n'
        elif self.source and not self.explain:
            template += '\n\n%(lines)s\n'
        elif self.explain and not self.source:
            template += '\n\n%(explanation)s\n\n'
        return template % dict((name, getattr(self, name)) for name in
                               ['filename', 'line', 'definition', 'message',
                                'explanation', 'lines'])

    __repr__ = __str__

    def __lt__(self, other):
        return (self.filename, self.line) < (other.filename, other.line)


class ErrorRegistry(object):
    groups = []

    class ErrorGroup(object):

        def __init__(self, prefix, name):
            self.prefix = prefix
            self.name = name
            self.errors = []

        def create_error(self, error_code, error_desc, error_context=None):
            # TODO: check prefix

            class _Error(Error):
                code = error_code
                short_desc = error_desc
                context = error_context

            self.errors.append(_Error)
            return _Error

    @classmethod
    def create_group(cls, prefix, name):
        group = cls.ErrorGroup(prefix, name)
        cls.groups.append(group)
        return group

    @classmethod
    def get_error_codes(cls):
        for group in cls.groups:
            for error in group.errors:
                yield error.code

    @classmethod
    def to_rst(cls):
        sep_line = '+' + 6 * '-' + '+' + '-' * 71 + '+\n'
        blank_line = '|' + 78 * ' ' + '|\n'
        table = ''
        for group in cls.groups:
            table += sep_line
            table += blank_line
            table += '|' + ('**%s**' % group.name).center(78) + '|\n'
            table += blank_line
            for error in group.errors:
                table += sep_line
                table += ('|' + error.code.center(6) + '| ' +
                          error.short_desc.ljust(70) + '|\n')
        table += sep_line
        return table


D1xx = ErrorRegistry.create_group('D1', 'Missing Docstrings')
D100 = D1xx.create_error('D100', 'Missing docstring in public module')
D101 = D1xx.create_error('D101', 'Missing docstring in public class')
D102 = D1xx.create_error('D102', 'Missing docstring in public method')
D103 = D1xx.create_error('D103', 'Missing docstring in public function')
D104 = D1xx.create_error('D104', 'Missing docstring in public package')
D105 = D1xx.create_error('D105', 'Missing docstring in magic method')

D2xx = ErrorRegistry.create_group('D2', 'Whitespace Issues')
D200 = D2xx.create_error('D200', 'One-line docstring should fit on one line '
                                 'with quotes', 'found %s')
D201 = D2xx.create_error('D201', 'No blank lines allowed before function '
                                 'docstring', 'found %s')
D202 = D2xx.create_error('D202', 'No blank lines allowed after function '
                                 'docstring', 'found %s')
D203 = D2xx.create_error('D203', '1 blank line required before class '
                                 'docstring', 'found %s')
D204 = D2xx.create_error('D204', '1 blank line required after class '
                                 'docstring', 'found %s')
D205 = D2xx.create_error('D205', '1 blank line required between summary line '
                                 'and description', 'found %s')
D206 = D2xx.create_error('D206', 'Docstring should be indented with spaces, '
                                 'not tabs')
D207 = D2xx.create_error('D207', 'Docstring is under-indented')
D208 = D2xx.create_error('D208', 'Docstring is over-indented')
D209 = D2xx.create_error('D209', 'Multi-line docstring closing quotes should '
                                 'be on a separate line')
D210 = D2xx.create_error('D210', 'No whitespaces allowed surrounding '
                                 'docstring text')
D211 = D2xx.create_error('D211', 'No blank lines allowed before class '
                                 'docstring', 'found %s')
D212 = D2xx.create_error('D212', 'Multi-line docstring summary should start '
                                 'at the first line')
D213 = D2xx.create_error('D213', 'Multi-line docstring summary should start '
                                 'at the second line')

D3xx = ErrorRegistry.create_group('D3', 'Quotes Issues')
D300 = D3xx.create_error('D300', 'Use """triple double quotes"""',
                         'found %s-quotes')
D301 = D3xx.create_error('D301', 'Use r""" if any backslashes in a docstring')
D302 = D3xx.create_error('D302', 'Use u""" for Unicode docstrings')

D4xx = ErrorRegistry.create_group('D4', 'Docstring Content Issues')
D400 = D4xx.create_error('D400', 'First line should end with a period',
                         'not %r')
D401 = D4xx.create_error('D401', 'First line should be in imperative mood',
                         '%r, not %r')
D402 = D4xx.create_error('D402', 'First line should not be the function\'s '
                                 '"signature"')
D403 = D4xx.create_error('D403', 'First word of the first line should be '
                                 'properly capitalized', '%r, not %r')
D404 = D4xx.create_error('D404', 'First word of the docstring should not '
                                 'be `This`')


class AttrDict(dict):
    def __getattr__(self, item):
        return self[item]


conventions = AttrDict({
    'pep257': set(ErrorRegistry.get_error_codes()) - set(['D203',
                                                          'D212',
                                                          'D213',
                                                          'D404'])
})


# General configurations for pydocstyle run.
RunConfiguration = namedtuple('RunConfiguration',
                              ('explain', 'source', 'debug',
                               'verbose', 'count'))


class IllegalConfiguration(Exception):
    """An exception for illegal configurations."""

    pass


# Check configuration - used by the ConfigurationParser class.
CheckConfiguration = namedtuple('CheckConfiguration',
                                ('checked_codes', 'match', 'match_dir'))


def check_initialized(method):
    """Check that the configuration object was initialized."""
    def _decorator(self, *args, **kwargs):
        if self._arguments is None or self._options is None:
            raise RuntimeError('using an uninitialized configuration')
        return method(self, *args, **kwargs)
    return _decorator


class ConfigurationParser(object):
    """Responsible for parsing configuration from files and CLI.

    There are 2 types of configurations: Run configurations and Check
    configurations.

    Run Configurations:
    ------------------
    Responsible for deciding things that are related to the user interface,
    e.g. verbosity, debug options, etc.
    All run configurations default to `False` and are decided only by CLI.

    Check Configurations:
    --------------------
    Configurations that are related to which files and errors will be checked.
    These are configurable in 2 ways: using the CLI, and using configuration
    files.

    Configuration files are nested within the file system, meaning that the
    closer a configuration file is to a checked file, the more relevant it will
    be. For instance, imagine this directory structure:

    A
    +-- tox.ini: sets `select=D100`
    +-- B
        +-- foo.py
        +-- tox.ini: sets `add-ignore=D100`

    Then `foo.py` will not be checked for `D100`.
    The configuration build algorithm is described in `self._get_config`.

    Note: If any of `BASE_ERROR_SELECTION_OPTIONS` was selected in the CLI, all
    configuration files will be ignored and each file will be checked for
    the error codes supplied in the CLI.

    """

    CONFIG_FILE_OPTIONS = ('convention', 'select', 'ignore', 'add-select',
                           'add-ignore', 'match', 'match-dir')
    BASE_ERROR_SELECTION_OPTIONS = ('ignore', 'select', 'convention')

    DEFAULT_MATCH_RE = '(?!test_).*\.py'
    DEFAULT_MATCH_DIR_RE = '[^\.].*'
    DEFAULT_CONVENTION = conventions.pep257

    PROJECT_CONFIG_FILES = (
        'setup.cfg',
        'tox.ini',
        '.pydocstyle',
        '.pydocstylerc',
        # The following is deprecated, but remains for backwards compatibility.
        '.pep257',
    )

    POSSIBLE_SECTION_NAMES = ('pydocstyle', 'pep257')

    def __init__(self):
        """Create a configuration parser."""
        self._cache = {}
        self._override_by_cli = None
        self._options = self._arguments = self._run_conf = None
        self._parser = self._create_option_parser()

    # ---------------------------- Public Methods -----------------------------

    def get_default_run_configuration(self):
        """Return a `RunConfiguration` object set with default values."""
        options, _ = self._parse_args([])
        return self._create_run_config(options)

    def parse(self):
        """Parse the configuration.

        If one of `BASE_ERROR_SELECTION_OPTIONS` was selected, overrides all
        error codes to check and disregards any error code related
        configurations from the configuration files.

        """
        self._options, self._arguments = self._parse_args()
        self._arguments = self._arguments or ['.']

        if not self._validate_options(self._options):
            raise IllegalConfiguration()

        self._run_conf = self._create_run_config(self._options)

        config = self._create_check_config(self._options, use_dafaults=False)
        self._override_by_cli = config

    @check_initialized
    def get_user_run_configuration(self):
        """Return the run configuration for the script."""
        return self._run_conf

    @check_initialized
    def get_files_to_check(self):
        """Generate files and error codes to check on each one.

        Walk dir trees under `self._arguments` and generate yield filnames
        that `match` under each directory that `match_dir`.
        The method locates the configuration for each file name and yields a
        tuple of (filename, [error_codes]).

        With every discovery of a new configuration file `IllegalConfiguration`
        might be raised.

        """
        def _get_matches(config):
            """Return the `match` and `match_dir` functions for `config`."""
            match_func = re(config.match + '$').match
            match_dir_func = re(config.match_dir + '$').match
            return match_func, match_dir_func

        for name in self._arguments:
            if os.path.isdir(name):
                for root, dirs, filenames in os.walk(name):
                    config = self._get_config(root)
                    match, match_dir = _get_matches(config)

                    # Skip any dirs that do not match match_dir
                    dirs[:] = [dir for dir in dirs if match_dir(dir)]

                    for filename in filenames:
                        if match(filename):
                            full_path = os.path.join(root, filename)
                            yield full_path, list(config.checked_codes)
            else:
                config = self._get_config(name)
                match, _ = _get_matches(config)
                if match(name):
                    yield name, list(config.checked_codes)

    # --------------------------- Private Methods -----------------------------

    def _get_config(self, node):
        """Get and cache the run configuration for `node`.

        If no configuration exists (not local and not for the parend node),
        returns and caches a default configuration.

        The algorithm:
        -------------
        * If the current directory's configuration exists in
           `self._cache` - return it.
        * If a configuration file does not exist in this directory:
          * If the directory is not a root directory:
            * Cache its configuration as this directory's and return it.
          * Else:
            * Cache a default configuration and return it.
        * Else:
          * Read the configuration file.
          * If a parent directory exists AND the configuration file
            allows inheritance:
            * Read the parent configuration by calling this function with the
              parent directory as `node`.
            * Merge the parent configuration with the current one and
              cache it.
        * If the user has specified one of `BASE_ERROR_SELECTION_OPTIONS` in
          the CLI - return the CLI configuration with the configuration match
          clauses
        * Set the `--add-select` and `--add-ignore` CLI configurations.

        """
        path = os.path.abspath(node)
        path = path if os.path.isdir(path) else os.path.dirname(path)

        if path in self._cache:
            return self._cache[path]

        config_file = self._get_config_file_in_folder(path)

        if config_file is None:
            parent_dir, tail = os.path.split(path)
            if tail:
                # No configuration file, simply take the parent's.
                config = self._get_config(parent_dir)
            else:
                # There's no configuration file and no parent directory.
                # Use the default configuration or the one given in the CLI.
                config = self._create_check_config(self._options)
        else:
            # There's a config file! Read it and merge if necessary.
            options, inherit = self._read_configuration_file(config_file)

            parent_dir, tail = os.path.split(path)
            if tail and inherit:
                # There is a parent dir and we should try to merge.
                parent_config = self._get_config(parent_dir)
                config = self._merge_configuration(parent_config, options)
            else:
                # No need to merge or parent dir does not exist.
                config = self._create_check_config(options)

        # Make the CLI always win
        final_config = {}
        for attr in CheckConfiguration._fields:
            cli_val = getattr(self._override_by_cli, attr)
            conf_val = getattr(config, attr)
            final_config[attr] = cli_val if cli_val is not None else conf_val

        config = CheckConfiguration(**final_config)

        self._set_add_options(config.checked_codes, self._options)
        self._cache[path] = config
        return self._cache[path]

    def _read_configuration_file(self, path):
        """Try to read and parse `path` as a configuration file.

        If the configurations were illegal (checked with
        `self._validate_options`), raises `IllegalConfiguration`.

        Returns (options, should_inherit).

        """
        parser = RawConfigParser()
        options = None
        should_inherit = True

        if parser.read(path) and self._get_section_name(parser):
            option_list = dict([(o.dest, o.type or o.action)
                                for o in self._parser.option_list])

            # First, read the default values
            new_options, _ = self._parse_args([])

            # Second, parse the configuration
            section_name = self._get_section_name(parser)
            for opt in parser.options(section_name):
                if opt == 'inherit':
                    should_inherit = parser.getboolean(section_name, opt)
                    continue

                if opt.replace('_', '-') not in self.CONFIG_FILE_OPTIONS:
                    log.warning("Unknown option '{0}' ignored".format(opt))
                    continue

                normalized_opt = opt.replace('-', '_')
                opt_type = option_list[normalized_opt]
                if opt_type in ('int', 'count'):
                    value = parser.getint(section_name, opt)
                elif opt_type == 'string':
                    value = parser.get(section_name, opt)
                else:
                    assert opt_type in ('store_true', 'store_false')
                    value = parser.getboolean(section_name, opt)
                setattr(new_options, normalized_opt, value)

            # Third, fix the set-options
            options = self._fix_set_options(new_options)

        if options is not None:
            if not self._validate_options(options):
                raise IllegalConfiguration('in file: {0}'.format(path))

        return options, should_inherit

    def _merge_configuration(self, parent_config, child_options):
        """Merge parent config into the child options.

        The migration process requires an `options` object for the child in
        order to distinguish between mutually exclusive codes, add-select and
        add-ignore error codes.

        """
        # Copy the parent error codes so we won't override them
        error_codes = copy.deepcopy(parent_config.checked_codes)
        if self._has_exclusive_option(child_options):
            error_codes = self._get_exclusive_error_codes(child_options)

        self._set_add_options(error_codes, child_options)

        match = child_options.match \
            if child_options.match is not None else parent_config.match
        match_dir = child_options.match_dir \
            if child_options.match_dir is not None else parent_config.match_dir

        return CheckConfiguration(checked_codes=error_codes,
                                  match=match,
                                  match_dir=match_dir)

    def _parse_args(self, args=None, values=None):
        """Parse the options using `self._parser` and reformat the options."""
        options, arguments = self._parser.parse_args(args, values)
        return self._fix_set_options(options), arguments

    @staticmethod
    def _create_run_config(options):
        """Create a `RunConfiguration` object from `options`."""
        values = dict([(opt, getattr(options, opt)) for opt in
                       RunConfiguration._fields])
        return RunConfiguration(**values)

    @classmethod
    def _create_check_config(cls, options, use_dafaults=True):
        """Create a `CheckConfiguration` object from `options`.

        If `use_dafaults`, any of the match options that are `None` will
        be replaced with their default value and the default convention will be
        set for the checked codes.

        """
        match = cls.DEFAULT_MATCH_RE \
            if options.match is None and use_dafaults \
            else options.match

        match_dir = cls.DEFAULT_MATCH_DIR_RE \
            if options.match_dir is None and use_dafaults \
            else options.match_dir

        checked_codes = None

        if cls._has_exclusive_option(options) or use_dafaults:
            checked_codes = cls._get_checked_errors(options)

        return CheckConfiguration(checked_codes=checked_codes,
                                  match=match, match_dir=match_dir)

    @classmethod
    def _get_section_name(cls, parser):
        """Parse options from relevant section."""
        for section_name in cls.POSSIBLE_SECTION_NAMES:
            if parser.has_section(section_name):
                return section_name

        return None

    @classmethod
    def _get_config_file_in_folder(cls, path):
        """Look for a configuration file in `path`.

        If exists return it's full path, otherwise None.

        """
        if os.path.isfile(path):
            path = os.path.dirname(path)

        for fn in cls.PROJECT_CONFIG_FILES:
            config = RawConfigParser()
            full_path = os.path.join(path, fn)
            if config.read(full_path) and cls._get_section_name(config):
                return full_path

    @staticmethod
    def _get_exclusive_error_codes(options):
        """Extract the error codes from the selected exclusive option."""
        codes = set(ErrorRegistry.get_error_codes())
        checked_codes = None

        if options.ignore is not None:
            checked_codes = codes - options.ignore
        elif options.select is not None:
            checked_codes = options.select
        elif options.convention is not None:
            checked_codes = getattr(conventions, options.convention)

        # To not override the conventions nor the options - copy them.
        return copy.deepcopy(checked_codes)

    @staticmethod
    def _set_add_options(checked_codes, options):
        """Set `checked_codes` by the `add_ignore` or `add_select` options."""
        checked_codes |= options.add_select
        checked_codes -= options.add_ignore

    @classmethod
    def _get_checked_errors(cls, options):
        """Extract the codes needed to be checked from `options`."""
        checked_codes = cls._get_exclusive_error_codes(options)
        if checked_codes is None:
            checked_codes = cls.DEFAULT_CONVENTION

        cls._set_add_options(checked_codes, options)

        return checked_codes

    @classmethod
    def _validate_options(cls, options):
        """Validate the mutually exclusive options.

        Return `True` iff only zero or one of `BASE_ERROR_SELECTION_OPTIONS`
        was selected.

        """
        for opt1, opt2 in \
                itertools.permutations(cls.BASE_ERROR_SELECTION_OPTIONS, 2):
            if getattr(options, opt1) and getattr(options, opt2):
                log.error('Cannot pass both {0} and {1}. They are '
                          'mutually exclusive.'.format(opt1, opt2))
                return False

        if options.convention and options.convention not in conventions:
            log.error("Illegal convention '{0}'. Possible conventions: {1}"
                      .format(options.convention,
                              ', '.join(conventions.keys())))
            return False
        return True

    @classmethod
    def _has_exclusive_option(cls, options):
        """Return `True` iff one or more exclusive options were selected."""
        return any([getattr(options, opt) is not None for opt in
                    cls.BASE_ERROR_SELECTION_OPTIONS])

    @staticmethod
    def _fix_set_options(options):
        """Alter the set options from None/strings to sets in place."""
        optional_set_options = ('ignore', 'select')
        mandatory_set_options = ('add_ignore', 'add_select')

        def _get_set(value_str):
            """Split `value_str` by the delimiter `,` and return a set.

            Removes any occurrences of '' in the set.

            """
            return set(value_str.split(',')) - set([''])

        for opt in optional_set_options:
            value = getattr(options, opt)
            if value is not None:
                setattr(options, opt, _get_set(value))

        for opt in mandatory_set_options:
            value = getattr(options, opt)
            if value is None:
                value = ''

            if not isinstance(value, Set):
                value = _get_set(value)

            setattr(options, opt, value)

        return options

    @classmethod
    def _create_option_parser(cls):
        """Return an option parser to parse the command line arguments."""
        from optparse import OptionParser

        parser = OptionParser(
            version=__version__,
            usage='Usage: pydocstyle [options] [<file|dir>...]')

        option = parser.add_option

        # Run configuration options
        option('-e', '--explain', action='store_true', default=False,
               help='show explanation of each error')
        option('-s', '--source', action='store_true', default=False,
               help='show source for each error')
        option('-d', '--debug', action='store_true', default=False,
               help='print debug information')
        option('-v', '--verbose', action='store_true', default=False,
               help='print status information')
        option('--count', action='store_true', default=False,
               help='print total number of errors to stdout')

        # Error check options
        option('--select', metavar='<codes>', default=None,
               help='choose the basic list of checked errors by '
                    'specifying which errors to check for (with a list of '
                    'comma-separated error codes). '
                    'for example: --select=D101,D202')
        option('--ignore', metavar='<codes>', default=None,
               help='choose the basic list of checked errors by '
                    'specifying which errors to ignore (with a list of '
                    'comma-separated error codes). '
                    'for example: --ignore=D101,D202')
        option('--convention', metavar='<name>', default=None,
               help='choose the basic list of checked errors by specifying an '
                    'existing convention. Possible conventions: {0}'
                    .format(', '.join(conventions)))
        option('--add-select', metavar='<codes>', default=None,
               help='amend the list of errors to check for by specifying '
                    'more error codes to check.')
        option('--add-ignore', metavar='<codes>', default=None,
               help='amend the list of errors to check for by specifying '
                    'more error codes to ignore.')

        # Match clauses
        option('--match', metavar='<pattern>', default=None,
               help=("check only files that exactly match <pattern> regular "
                     "expression; default is --match='{0}' which matches "
                     "files that don't start with 'test_' but end with "
                     "'.py'").format(cls.DEFAULT_MATCH_RE))
        option('--match-dir', metavar='<pattern>', default=None,
               help=("search only dirs that exactly match <pattern> regular "
                     "expression; default is --match-dir='{0}', which "
                     "matches all dirs that don't start with "
                     "a dot").format(cls.DEFAULT_MATCH_DIR_RE))

        return parser


def check(filenames, select=None, ignore=None):
    """Generate PEP 257 errors that exist in `filenames` iterable.

    Only returns errors with error-codes defined in `checked_codes` iterable.

    Example
    -------
    >>> check([ppydocstyle.py.py], checked_codes=['D100'])
    <generator object check at 0x...>

    """
    if select is not None and ignore is not None:
        raise IllegalConfiguration('Cannot pass both select and ignore. '
                                   'They are mutually exclusive.')
    elif select is not None:
        checked_codes = select
    elif ignore is not None:
        checked_codes = list(set(ErrorRegistry.get_error_codes()) -
                             set(ignore))
    else:
        checked_codes = conventions.pep257

    for filename in filenames:
        log.info('Checking file %s.', filename)
        try:
            with tokenize_open(filename) as file:
                source = file.read()
            for error in PEP257Checker().check_source(source, filename):
                code = getattr(error, 'code', None)
                if code in checked_codes:
                    yield error
        except (EnvironmentError, AllError):
            yield sys.exc_info()[1]
        except tk.TokenError:
            yield SyntaxError('invalid syntax in file %s' % filename)


def setup_stream_handlers(conf):
    """Setup logging stream handlers according to the options."""
    class StdoutFilter(logging.Filter):
        def filter(self, record):
            return record.levelno in (logging.DEBUG, logging.INFO)

    log.handlers = []

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.WARNING)
    stdout_handler.addFilter(StdoutFilter())
    if conf.debug:
        stdout_handler.setLevel(logging.DEBUG)
    elif conf.verbose:
        stdout_handler.setLevel(logging.INFO)
    else:
        stdout_handler.setLevel(logging.WARNING)
    log.addHandler(stdout_handler)

    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.WARNING)
    log.addHandler(stderr_handler)


def run_pydocstyle(use_pep257=False):
    log.setLevel(logging.DEBUG)
    conf = ConfigurationParser()
    setup_stream_handlers(conf.get_default_run_configuration())

    try:
        conf.parse()
    except IllegalConfiguration:
        return ReturnCode.invalid_options

    run_conf = conf.get_user_run_configuration()

    # Reset the logger according to the command line arguments
    setup_stream_handlers(run_conf)

    if use_pep257:
        log.warning("Deprecation Warning:\n"
                    "pep257 has been renamed to pydocstyle and the use of the "
                    "pep257 executable is deprecated and will be removed in "
                    "the next major version. Please use `pydocstyle` instead.")

    log.debug("starting in debug mode.")

    Error.explain = run_conf.explain
    Error.source = run_conf.source

    errors = []
    try:
        for filename, checked_codes in conf.get_files_to_check():
            errors.extend(check((filename,), select=checked_codes))
    except IllegalConfiguration:
        # An illegal configuration file was found during file generation.
        return ReturnCode.invalid_options

    code = ReturnCode.no_violations_found
    count = 0
    for error in errors:
        sys.stderr.write('%s\n' % error)
        code = ReturnCode.violations_found
        count += 1
    if run_conf.count:
        print(count)
    return code


parse = Parser()


def check_for(kind, terminal=False):
    def decorator(f):
        f._check_for = kind
        f._terminal = terminal
        return f
    return decorator


class PEP257Checker(object):
    """Checker for PEP 257.

    D10x: Missing docstrings
    D20x: Whitespace issues
    D30x: Docstring formatting
    D40x: Docstring content issues

    """

    def check_source(self, source, filename):
        module = parse(StringIO(source), filename)
        for definition in module:
            for check in self.checks:
                terminate = False
                if isinstance(definition, check._check_for):
                    error = check(None, definition, definition.docstring)
                    errors = error if hasattr(error, '__iter__') else [error]
                    for error in errors:
                        if error is not None:
                            partition = check.__doc__.partition('.\n')
                            message, _, explanation = partition
                            error.set_context(explanation=explanation,
                                              definition=definition)
                            yield error
                            if check._terminal:
                                terminate = True
                                break
                if terminate:
                    break

    @property
    def checks(self):
        all = [check for check in vars(type(self)).values()
               if hasattr(check, '_check_for')]
        return sorted(all, key=lambda check: not check._terminal)

    @check_for(Definition, terminal=True)
    def check_docstring_missing(self, definition, docstring):
        """D10{0,1,2,3}: Public definitions should have docstrings.

        All modules should normally have docstrings.  [...] all functions and
        classes exported by a module should also have docstrings. Public
        methods (including the __init__ constructor) should also have
        docstrings.

        Note: Public (exported) definitions are either those with names listed
              in __all__ variable (if present), or those that do not start
              with a single underscore.

        """
        if (not docstring and definition.is_public or
                docstring and is_blank(ast.literal_eval(docstring))):
            codes = {Module: D100, Class: D101, NestedClass: D101,
                     Method: (lambda: D105() if is_magic(definition.name)
                              else D102()),
                     Function: D103, NestedFunction: D103, Package: D104}
            return codes[type(definition)]()

    @check_for(Definition)
    def check_one_liners(self, definition, docstring):
        """D200: One-liner docstrings should fit on one line with quotes.

        The closing quotes are on the same line as the opening quotes.
        This looks better for one-liners.

        """
        if docstring:
            lines = ast.literal_eval(docstring).split('\n')
            if len(lines) > 1:
                non_empty_lines = sum(1 for l in lines if not is_blank(l))
                if non_empty_lines == 1:
                    return D200(len(lines))

    @check_for(Function)
    def check_no_blank_before(self, function, docstring):  # def
        """D20{1,2}: No blank lines allowed around function/method docstring.

        There's no blank line either before or after the docstring.

        """
        if docstring:
            before, _, after = function.source.partition(docstring)
            blanks_before = list(map(is_blank, before.split('\n')[:-1]))
            blanks_after = list(map(is_blank, after.split('\n')[1:]))
            blanks_before_count = sum(takewhile(bool, reversed(blanks_before)))
            blanks_after_count = sum(takewhile(bool, blanks_after))
            if blanks_before_count != 0:
                yield D201(blanks_before_count)
            if not all(blanks_after) and blanks_after_count != 0:
                yield D202(blanks_after_count)

    @check_for(Class)
    def check_blank_before_after_class(self, class_, docstring):
        """D20{3,4}: Class docstring should have 1 blank line around them.

        Insert a blank line before and after all docstrings (one-line or
        multi-line) that document a class -- generally speaking, the class's
        methods are separated from each other by a single blank line, and the
        docstring needs to be offset from the first method by a blank line;
        for symmetry, put a blank line between the class header and the
        docstring.

        """
        # NOTE: this gives false-positive in this case
        # class Foo:
        #
        #     """Docstring."""
        #
        #
        # # comment here
        # def foo(): pass
        if docstring:
            before, _, after = class_.source.partition(docstring)
            blanks_before = list(map(is_blank, before.split('\n')[:-1]))
            blanks_after = list(map(is_blank, after.split('\n')[1:]))
            blanks_before_count = sum(takewhile(bool, reversed(blanks_before)))
            blanks_after_count = sum(takewhile(bool, blanks_after))
            if blanks_before_count != 0:
                yield D211(blanks_before_count)
            if blanks_before_count != 1:
                yield D203(blanks_before_count)
            if not all(blanks_after) and blanks_after_count != 1:
                yield D204(blanks_after_count)

    @check_for(Definition)
    def check_blank_after_summary(self, definition, docstring):
        """D205: Put one blank line between summary line and description.

        Multi-line docstrings consist of a summary line just like a one-line
        docstring, followed by a blank line, followed by a more elaborate
        description. The summary line may be used by automatic indexing tools;
        it is important that it fits on one line and is separated from the
        rest of the docstring by a blank line.

        """
        if docstring:
            lines = ast.literal_eval(docstring).strip().split('\n')
            if len(lines) > 1:
                post_summary_blanks = list(map(is_blank, lines[1:]))
                blanks_count = sum(takewhile(bool, post_summary_blanks))
                if blanks_count != 1:
                    return D205(blanks_count)

    @check_for(Definition)
    def check_indent(self, definition, docstring):
        """D20{6,7,8}: The entire docstring should be indented same as code.

        The entire docstring is indented the same as the quotes at its
        first line.

        """
        if docstring:
            before_docstring, _, _ = definition.source.partition(docstring)
            _, _, indent = before_docstring.rpartition('\n')
            lines = docstring.split('\n')
            if len(lines) > 1:
                lines = lines[1:]  # First line does not need indent.
                indents = [leading_space(l) for l in lines if not is_blank(l)]
                if set(' \t') == set(''.join(indents) + indent):
                    yield D206()
                if (len(indents) > 1 and min(indents[:-1]) > indent or
                        indents[-1] > indent):
                    yield D208()
                if min(indents) < indent:
                    yield D207()

    @check_for(Definition)
    def check_newline_after_last_paragraph(self, definition, docstring):
        """D209: Put multi-line docstring closing quotes on separate line.

        Unless the entire docstring fits on a line, place the closing
        quotes on a line by themselves.

        """
        if docstring:
            lines = [l for l in ast.literal_eval(docstring).split('\n')
                     if not is_blank(l)]
            if len(lines) > 1:
                if docstring.split("\n")[-1].strip() not in ['"""', "'''"]:
                    return D209()

    @check_for(Definition)
    def check_surrounding_whitespaces(self, definition, docstring):
        """D210: No whitespaces allowed surrounding docstring text."""
        if docstring:
            lines = ast.literal_eval(docstring).split('\n')
            if lines[0].startswith(' ') or \
                    len(lines) == 1 and lines[0].endswith(' '):
                return D210()

    @check_for(Definition)
    def check_multi_line_summary_start(self, definition, docstring):
        """D21{2,3}: Multi-line docstring summary style check.

        A multi-line docstring summary should start either at the first,
        or separately at the second line of a docstring.

        """
        if docstring:
            start_triple = [
                '"""', "'''",
                'u"""', "u'''",
                'r"""', "r'''",
                'ur"""', "ur'''"
            ]

            lines = ast.literal_eval(docstring).split('\n')
            if len(lines) > 1:
                first = docstring.split("\n")[0].strip().lower()
                if first in start_triple:
                    return D212()
                else:
                    return D213()

    @check_for(Definition)
    def check_triple_double_quotes(self, definition, docstring):
        r'''D300: Use """triple double quotes""".

        For consistency, always use """triple double quotes""" around
        docstrings. Use r"""raw triple double quotes""" if you use any
        backslashes in your docstrings. For Unicode docstrings, use
        u"""Unicode triple-quoted strings""".

        Note: Exception to this is made if the docstring contains
              """ quotes in its body.

        '''
        if docstring:
            opening = docstring[:5].lower()
            if '"""' in ast.literal_eval(docstring) and opening.startswith(
                    ("'''", "r'''", "u'''", "ur'''")):
                # Allow ''' quotes if docstring contains """, because
                # otherwise """ quotes could not be expressed inside
                # docstring. Not in PEP 257.
                return
            if not opening.startswith(('"""', 'r"""', 'u"""', 'ur"""')):
                quotes = "'''" if "'''" in opening else "'"
                return D300(quotes)

    @check_for(Definition)
    def check_backslashes(self, definition, docstring):
        r'''D301: Use r""" if any backslashes in a docstring.

        Use r"""raw triple double quotes""" if you use any backslashes
        (\) in your docstrings.

        '''
        # Just check that docstring is raw, check_triple_double_quotes
        # ensures the correct quotes.
        if docstring and '\\' in docstring and not docstring.startswith(
                ('r', 'ur')):
            return D301()

    @check_for(Definition)
    def check_unicode_docstring(self, definition, docstring):
        r'''D302: Use u""" for docstrings with Unicode.

        For Unicode docstrings, use u"""Unicode triple-quoted strings""".

        '''
        if definition.module.future_imports['unicode_literals']:
            return

        # Just check that docstring is unicode, check_triple_double_quotes
        # ensures the correct quotes.
        if docstring and sys.version_info[0] <= 2:
            if not is_ascii(docstring) and not docstring.startswith(
                    ('u', 'ur')):
                return D302()

    @check_for(Definition)
    def check_ends_with_period(self, definition, docstring):
        """D400: First line should end with a period.

        The [first line of a] docstring is a phrase ending in a period.

        """
        if docstring:
            summary_line = ast.literal_eval(docstring).strip().split('\n')[0]
            if not summary_line.endswith('.'):
                return D400(summary_line[-1])

    @check_for(Function)
    def check_imperative_mood(self, function, docstring):  # def context
        """D401: First line should be in imperative mood: 'Do', not 'Does'.

        [Docstring] prescribes the function or method's effect as a command:
        ("Do this", "Return that"), not as a description; e.g. don't write
        "Returns the pathname ...".

        """
        if docstring:
            stripped = ast.literal_eval(docstring).strip()
            if stripped:
                first_word = stripped.split()[0]
                if first_word.endswith('s') and not first_word.endswith('ss'):
                    return D401(first_word[:-1], first_word)

    @check_for(Function)
    def check_no_signature(self, function, docstring):  # def context
        """D402: First line should not be function's or method's "signature".

        The one-line docstring should NOT be a "signature" reiterating the
        function/method parameters (which can be obtained by introspection).

        """
        if docstring:
            first_line = ast.literal_eval(docstring).strip().split('\n')[0]
            if function.name + '(' in first_line.replace(' ', ''):
                return D402()

    @check_for(Function)
    def check_capitalized(self, function, docstring):
        """D403: First word of the first line should be properly capitalized.

        The [first line of a] docstring is a phrase ending in a period.

        """
        if docstring:
            first_word = ast.literal_eval(docstring).split()[0]
            if first_word == first_word.upper():
                return
            for char in first_word:
                if char not in string.ascii_letters and char != "'":
                    return
            if first_word != first_word.capitalize():
                return D403(first_word.capitalize(), first_word)

    @check_for(Definition)
    def check_starts_with_this(self, function, docstring):
        """D404: First word of the docstring should not be `This`.

        Docstrings should use short, simple language. They should not begin
        with "This class is [..]" or "This module contains [..]".

        """
        if docstring:
            first_word = ast.literal_eval(docstring).split()[0]
            if first_word.lower() == 'this':
                return D404()

    # Somewhat hard to determine if return value is mentioned.
    # @check(Function)
    def SKIP_check_return_type(self, function, docstring):
        """D40x: Return value type should be mentioned.

        [T]he nature of the return value cannot be determined by
        introspection, so it should be mentioned.

        """
        if docstring and function.returns_value:
            if 'return' not in docstring.lower():
                return Error()


def main(use_pep257=False):
    try:
        sys.exit(run_pydocstyle(use_pep257))
    except KeyboardInterrupt:
        pass


def main_pep257():
    main(use_pep257=True)


if __name__ == '__main__':
    main()
