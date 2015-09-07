#! /usr/bin/env python
"""Static analysis tool for checking docstring conventions and style.

Implemented checks cover PEP257:
http://www.python.org/dev/peps/pep-0257/

Other checks can be added, e.g. NumPy docstring conventions:
https://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt

The repository is located at:
http://github.com/GreenSteam/pep257

"""
from __future__ import with_statement

import os
import sys
import logging
import tokenize as tk
from itertools import takewhile, dropwhile, chain
from optparse import OptionParser
from re import compile as re
import itertools

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


__version__ = '0.6.1-alpha'
__all__ = ('check', 'collect')

PROJECT_CONFIG = ('setup.cfg', 'tox.ini', '.pep257')
NO_VIOLATIONS_RETURN_CODE = 0
VIOLATIONS_RETURN_CODE = 1
INVALID_OPTIONS_RETURN_CODE = 2


def humanize(string):
    return re(r'(.)([A-Z]+)').sub(r'\1 \2', string).lower()


def is_magic(name):
    return name.startswith('__') and name.endswith('__')


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
        kwargs = ', '.join('{}={!r}'.format(field, getattr(self, field))
                           for field in self._fields)
        return '{}({})'.format(self.__class__.__name__, kwargs)


class Definition(Value):

    _fields = ('name', '_source', 'start', 'end', 'decorators', 'docstring',
               'children', 'parent')

    _human = property(lambda self: humanize(type(self).__name__))
    kind = property(lambda self: self._human.split()[-1])
    module = property(lambda self: self.parent.module)
    all = property(lambda self: self.module.all)
    _slice = property(lambda self: slice(self.start - 1, self.end))
    source = property(lambda self: ''.join(self._source[self._slice]))

    def __iter__(self):
        return chain([self], *self.children)

    @property
    def _publicity(self):
        return {True: 'public', False: 'private'}[self.is_public]

    def __str__(self):
        return 'in %s %s `%s`' % (self._publicity, self._human, self.name)


class Module(Definition):

    _fields = ('name', '_source', 'start', 'end', 'decorators', 'docstring',
               'children', 'parent', '_all')
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
        else:  # TODO: are there any magic functions? not methods
            return not self.name.startswith('_') or is_magic(self.name)


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
        name_is_public = not self.name.startswith('_') or is_magic(self.name)
        return self.parent.is_public and name_is_public


class Class(Definition):

    _nest = staticmethod(lambda s: {'def': Method, 'class': NestedClass}[s])
    is_public = Function.is_public


class NestedClass(Class):

    is_public = False


class Decorator(Value):

    """A decorator for function, method or class."""

    _fields = 'name arguments'.split()


class TokenKind(int):
    def __repr__(self):
        return "tk.{}".format(tk.tok_name[self])


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
            'That means pep257 cannot decide which definitions are public. '
            'Variable __all__ should be present at most once in each file, '
            "in form `__all__ = ('a_public_function', 'APublicClass', ...)`. "
            'More info on __all__: http://stackoverflow.com/q/44834/. ')


class Parser(object):

    def __call__(self, filelike, filename):
        self.source = filelike.readlines()
        src = ''.join(self.source)
        self.stream = TokenStream(StringIO(src))
        self.filename = filename
        self.all = None
        self._accumulated_decorators = []
        return self.parse_module()

    current = property(lambda self: self.stream.current)
    line = property(lambda self: self.stream.line)

    def consume(self, kind):
        assert self.stream.move().kind == kind

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
        """Parse multiple defintions and yield them."""
        while self.current is not None:
            log.debug("parsing defintion list, current token is %r (%s)",
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
                   "pep257 cannot reliably detect contents of the __all__ "
                   "variable, because it can be mutated. Change __all__ to be "
                   "an (immutable) tuple, to remove this warning. Note, "
                   "pep257 uses __all__ to detect which definitions are "
                   "public, to warn if public definitions are missing "
                   "docstrings. If __all__ is a (mutable) list, pep257 cannot "
                   "reliably assume its contents. pep257 will proceed "
                   "assuming __all__ is not mutated.\n" % self.filename)
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
                kind = token.tok_name[self.current.kind]
                raise AllError('Unexpected token kind in  __all__: %s' % kind)
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
        log.debug("finished parsing module.")
        return module

    def parse_definition(self, class_):
        """Parse a defintion and return its value in a `class_` object."""
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
            log.debug("parsing nested defintions.")
            children = list(self.parse_definitions(class_))
            log.debug("finished parsing nested defintions for '%s'", name)
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


class Conventions(object):
    pep257 = set(ErrorRegistry.get_error_codes())


def get_option_parser():
    parser = OptionParser(version=__version__,
                          usage='Usage: pep257 [options] [<file|dir>...]')
    parser.config_options = ('explain', 'source', 'ignore', 'match', 'select',
                             'match-dir', 'debug', 'verbose', 'count',
                             'convention')
    option = parser.add_option
    option('-e', '--explain', action='store_true',
           help='show explanation of each error')
    option('-s', '--source', action='store_true',
           help='show source for each error')
    option('--select', metavar='<codes>', default='',
           help='choose the basic list of checked errors by specifying which '
                'errors to check for (with a list of comma-separated error '
                'codes). for example: --select=D101,D202')
    option('--ignore', metavar='<codes>', default='',
           help='choose the basic list of checked errors by specifying which '
                'errors to ignore (with a list of comma-separated error '
                'codes). for example: --ignore=D101,D202')
    option('--convention', metavar='<name>', default='',
           help='choose the basic list of checked errors by specifying an '
                'existing convention. for example: --convention=pep257')
    option('--add-select', metavar='<codes>', default='',
           help='amend the list of errors to check for by specifying more '
                'error codes to check.')
    option('--add-ignore', metavar='<codes>', default='',
           help='amend the list of errors to check for by specifying more '
                'error codes to ignore.')
    option('--match', metavar='<pattern>', default='(?!test_).*\.py',
           help="check only files that exactly match <pattern> regular "
                "expression; default is --match='(?!test_).*\.py' which "
                "matches files that don't start with 'test_' but end with "
                "'.py'")
    option('--match-dir', metavar='<pattern>', default='[^\.].*',
           help="search only dirs that exactly match <pattern> regular "
                "expression; default is --match-dir='[^\.].*', which matches "
                "all dirs that don't start with a dot")
    option('-d', '--debug', action='store_true',
           help='print debug information')
    option('-v', '--verbose', action='store_true',
           help='print status information')
    option('--count', action='store_true',
           help='print total number of errors to stdout')
    return parser


def collect(names, match=lambda name: True, match_dir=lambda name: True):
    """Walk dir trees under `names` and generate filnames that `match`.

    Example
    -------
    >>> sorted(collect(['non-dir.txt', './'],
    ...                match=lambda name: name.endswith('.py')))
    ['non-dir.txt', './pep257.py', './setup.py', './test_pep257.py']

    """
    for name in names:  # map(expanduser, names):
        if os.path.isdir(name):
            for root, dirs, filenames in os.walk(name):
                # Skip any dirs that do not match match_dir
                dirs[:] = [dir for dir in dirs if match_dir(dir)]
                for filename in filenames:
                    if match(filename):
                        yield os.path.join(root, filename)
        else:
            yield name


def check(filenames, select=None, ignore=None):
    """Generate PEP 257 errors that exist in `filenames` iterable.

    Only returns errors with error-codes defined in `checked_codes` iterable.

    Example
    -------
    >>> check(['pep257.py'], checked_codes=['D100'])
    <generator object check at 0x...>

    """
    if select and ignore:
        raise ValueError('Cannot pass both select and ignore. They are '
                         'mutually exclusive.')
    elif select or ignore:
        checked_codes = (select or
                         set(ErrorRegistry.get_error_codes()) - set(ignore))
    else:
        checked_codes = Conventions.pep257

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


def get_options(args, opt_parser):
    config = RawConfigParser()
    parent = tail = os.path.abspath(os.path.commonprefix(args))
    config_found = False
    while tail and not config_found:
        log.info(tail)
        for fn in PROJECT_CONFIG:
            full_path = os.path.join(parent, fn)
            if config.read(full_path):
                log.info('local configuration: in %s.', full_path)
                config_found = True
                break
        parent, tail = os.path.split(parent)

    new_options = None
    if config.has_section('pep257'):
        option_list = dict([(o.dest, o.type or o.action)
                            for o in opt_parser.option_list])

        # First, read the default values
        new_options, _ = opt_parser.parse_args([])

        # Second, parse the configuration
        pep257_section = 'pep257'
        for opt in config.options(pep257_section):
            if opt.replace('_', '-') not in opt_parser.config_options:
                log.warning("Unknown option '{}' ignored".format(opt))
                continue
            normalized_opt = opt.replace('-', '_')
            opt_type = option_list[normalized_opt]
            if opt_type in ('int', 'count'):
                value = config.getint(pep257_section, opt)
            elif opt_type == 'string':
                value = config.get(pep257_section, opt)
            else:
                assert opt_type in ('store_true', 'store_false')
                value = config.getboolean(pep257_section, opt)
            setattr(new_options, normalized_opt, value)

    # Third, overwrite with the command-line options
    options, _ = opt_parser.parse_args(values=new_options)
    log.debug("options: %s", options)
    return options


def setup_stream_handlers(options):
    """Setup logging stream handlers according to the options."""
    class StdoutFilter(logging.Filter):
        def filter(self, record):
            return record.levelno in (logging.DEBUG, logging.INFO)

    if log.handlers:
        for handler in log.handlers:
            log.removeHandler(handler)

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.WARNING)
    stdout_handler.addFilter(StdoutFilter())
    if options.debug:
        stdout_handler.setLevel(logging.DEBUG)
    elif options.verbose:
        stdout_handler.setLevel(logging.INFO)
    else:
        stdout_handler.setLevel(logging.WARNING)
    log.addHandler(stdout_handler)

    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.WARNING)
    log.addHandler(stderr_handler)


def get_checked_error_codes(options):
    codes = set(ErrorRegistry.get_error_codes())
    if options.ignore:
        checked_codes = codes - set(options.ignore.split(','))
    elif options.select:
        checked_codes = set(options.select.split(','))
    elif options.convention:
        checked_codes = getattr(Conventions, options.convention)
    else:
        checked_codes = Conventions.pep257
    checked_codes -= set(options.add_ignore.split(','))
    checked_codes |= set(options.add_select.split(','))
    return checked_codes - set('')


def validate_options(options):
    mutually_exclusive = ('ignore', 'select', 'convention')
    for opt1, opt2 in itertools.permutations(mutually_exclusive, 2):
        if getattr(options, opt1) and getattr(options, opt2):
            log.error('Cannot pass both {0} and {1}. They are '
                      'mutually exclusive.'.format(opt1, opt2))
            return False
    if options.convention and not hasattr(Conventions, options.convention):
        return False
    return True


def run_pep257():
    log.setLevel(logging.DEBUG)
    opt_parser = get_option_parser()
    # setup the logger before parsing the config file, so that command line
    # arguments for debug / verbose will be printed.
    options, arguments = opt_parser.parse_args()
    setup_stream_handlers(options)
    # We parse the files before opening the config file, since it changes where
    # we look for the file.
    options = get_options(arguments, opt_parser)
    if not validate_options(options):
        return INVALID_OPTIONS_RETURN_CODE
    # Setup the handler again with values from the config file.
    setup_stream_handlers(options)

    collected = collect(arguments or ['.'],
                        match=re(options.match + '$').match,
                        match_dir=re(options.match_dir + '$').match)

    log.debug("starting pep257 in debug mode.")

    Error.explain = options.explain
    Error.source = options.source
    collected = list(collected)
    checked_codes = get_checked_error_codes(options)
    errors = check(collected, select=checked_codes)
    code = NO_VIOLATIONS_RETURN_CODE
    count = 0
    for error in errors:
        sys.stderr.write('%s\n' % error)
        code = VIOLATIONS_RETURN_CODE
        count += 1
    if options.count:
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
                docstring and is_blank(eval(docstring))):
            codes = {Module: D100, Class: D101, NestedClass: D101,
                     Method: D102, Function: D103, NestedFunction: D103,
                     Package: D104}
            return codes[type(definition)]()

    @check_for(Definition)
    def check_one_liners(self, definition, docstring):
        """D200: One-liner docstrings should fit on one line with quotes.

        The closing quotes are on the same line as the opening quotes.
        This looks better for one-liners.

        """
        if docstring:
            lines = eval(docstring).split('\n')
            if len(lines) > 1:
                non_empty_lines = sum(1 for l in lines if not is_blank(l))
                if non_empty_lines == 1:
                    return D200(len(lines))

    @check_for(Function)
    def check_no_blank_before(self, function, docstring):  # def
        """D20{1,2}: No blank lines allowed around function/method docstring.

        There's no blank line either before or after the docstring.

        """
        # NOTE: This does not take comments into account.
        # NOTE: This does not take into account functions with groups of code.
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
    def check_blank_before_after_class(slef, class_, docstring):
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
            lines = eval(docstring).strip().split('\n')
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
            lines = [l for l in eval(docstring).split('\n') if not is_blank(l)]
            if len(lines) > 1:
                if docstring.split("\n")[-1].strip() not in ['"""', "'''"]:
                    return D209()

    @check_for(Definition)
    def check_surrounding_whitespaces(self, definition, docstring):
        """D210: No whitespaces allowed surrounding docstring text."""
        if docstring:
            lines = eval(docstring).split('\n')
            if lines[0].startswith(' ') or \
                    len(lines) == 1 and lines[0].endswith(' '):
                return D210()

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
        if docstring and '"""' in eval(docstring) and docstring.startswith(
                ("'''", "r'''", "u'''", "ur'''")):
            # Allow ''' quotes if docstring contains """, because otherwise """
            # quotes could not be expressed inside docstring.  Not in PEP 257.
            return
        if docstring and not docstring.startswith(
                ('"""', 'r"""', 'u"""', 'ur"""')):
            quotes = "'''" if "'''" in docstring[:4] else "'"
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
            summary_line = eval(docstring).strip().split('\n')[0]
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
            stripped = eval(docstring).strip()
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
            first_line = eval(docstring).strip().split('\n')[0]
            if function.name + '(' in first_line.replace(' ', ''):
                return D402()

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


def main():
    try:
        sys.exit(run_pep257())
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
