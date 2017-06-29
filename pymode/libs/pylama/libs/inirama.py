"""
    Inirama is a python module that parses INI files.

    .. _badges:
    .. include:: ../README.rst
        :start-after: .. _badges:
        :end-before: .. _contents:

    .. _description:
    .. include:: ../README.rst
        :start-after: .. _description:
        :end-before: .. _badges:

    :copyright: 2013 by Kirill Klenov.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import unicode_literals, print_function


__version__ = "0.8.0"
__project__ = "Inirama"
__author__ = "Kirill Klenov <horneds@gmail.com>"
__license__ = "BSD"


import io
import re
import logging
try:
    from collections import OrderedDict
except ImportError:
    from UserDict import DictMixin

    class OrderedDict(dict, DictMixin):

        null = object()

        def __init__(self, *args, **kwargs):
            self.clear()
            self.update(*args, **kwargs)

        def clear(self):
            self.__map = dict()
            self.__order = list()
            dict.clear(self)

    def __setitem__(self, key, value):
        if key not in self:
            self.__map[key] = len(self.__order)
            self.__order.append(key)
        dict.__setitem__(self, key, value)

    def __delitem__(self, key):
        dict.__delitem__(self, key)
        self.__map.pop(key)
        self.__order = self.null

    def __iter__(self):
        for key in self.__order:
            if key is not self.null:
                yield key

    def keys(self):
        return list(self)

    setdefault = DictMixin.setdefault
    update = DictMixin.update
    pop = DictMixin.pop
    values = DictMixin.values
    items = DictMixin.items
    iterkeys = DictMixin.iterkeys
    itervalues = DictMixin.itervalues
    iteritems = DictMixin.iteritems


NS_LOGGER = logging.getLogger('inirama')


class Scanner(object):

    """ Split a code string on tokens. """

    def __init__(self, source, ignore=None, patterns=None):
        """ Init Scanner instance.

        :param patterns: List of token patterns [(token, regexp)]
        :param ignore: List of ignored tokens

        """
        self.reset(source)
        if patterns:
            self.patterns = []
            for k, r in patterns:
                self.patterns.append((k, re.compile(r)))

        if ignore:
            self.ignore = ignore

    def reset(self, source):
        """ Reset scanner's state.

        :param source: Source for parsing

        """
        self.tokens = []
        self.source = source
        self.pos = 0

    def scan(self):
        """ Scan source and grab tokens. """

        self.pre_scan()

        token = None
        end = len(self.source)

        while self.pos < end:

            best_pat = None
            best_pat_len = 0

            # Check patterns
            for p, regexp in self.patterns:
                m = regexp.match(self.source, self.pos)
                if m:
                    best_pat = p
                    best_pat_len = len(m.group(0))
                    break

            if best_pat is None:
                raise SyntaxError(
                    "SyntaxError[@char {0}: {1}]".format(
                        self.pos, "Bad token."))

            # Ignore patterns
            if best_pat in self.ignore:
                self.pos += best_pat_len
                continue

            # Create token
            token = (
                best_pat,
                self.source[self.pos:self.pos + best_pat_len],
                self.pos,
                self.pos + best_pat_len,
            )

            self.pos = token[-1]
            self.tokens.append(token)

    def pre_scan(self):
        """ Prepare source. """
        pass

    def __repr__(self):
        """ Print the last 5 tokens that have been scanned in.

        :return str:

        """
        return '<Scanner: ' + ','.join(
            "{0}({2}:{3})".format(*t) for t in self.tokens[-5:]) + ">"


class INIScanner(Scanner):

    """ Get tokens for INI. """

    patterns = [
        ('SECTION', re.compile(r'\[[^]]+\]')),
        ('IGNORE', re.compile(r'[ \r\t\n]+')),
        ('COMMENT', re.compile(r'[;#].*')),
        ('KEY_VALUE', re.compile(r'[^=\s]+\s*[:=].*')),
        ('CONTINUATION', re.compile(r'.*'))
    ]

    ignore = ['IGNORE']

    def pre_scan(self):
        """ Prepare string for scanning. """
        escape_re = re.compile(r'\\\n[\t ]+')
        self.source = escape_re.sub('', self.source)


undefined = object()


class Section(OrderedDict):

    """ Representation of INI section. """

    def __init__(self, namespace, *args, **kwargs):
        super(Section, self).__init__(*args, **kwargs)
        self.namespace = namespace

    def __setitem__(self, name, value):
        value = str(value)
        if value.isdigit():
            value = int(value)

        super(Section, self).__setitem__(name, value)


class InterpolationSection(Section):

    """ INI section with interpolation support. """

    var_re = re.compile('{([^}]+)}')

    def get(self, name, default=None):
        """ Get item by name.

        :return object: value or None if name not exists

        """

        if name in self:
            return self[name]
        return default

    def __interpolate__(self, math):
        try:
            key = math.group(1).strip()
            return self.namespace.default.get(key) or self[key]
        except KeyError:
            return ''

    def __getitem__(self, name, raw=False):
        value = super(InterpolationSection, self).__getitem__(name)
        if not raw:
            sample = undefined
            while sample != value:
                try:
                    sample, value = value, self.var_re.sub(
                        self.__interpolate__, value)
                except RuntimeError:
                    message = "Interpolation failed: {0}".format(name)
                    NS_LOGGER.error(message)
                    raise ValueError(message)
        return value

    def iteritems(self, raw=False):
        """ Iterate self items. """

        for key in self:
            yield key, self.__getitem__(key, raw=raw)

    items = iteritems


class Namespace(object):

    """ Default class for parsing INI.

    :param **default_items: Default items for default section.

    Usage
    -----

    ::

        from inirama import Namespace

        ns = Namespace()
        ns.read('config.ini')

        print ns['section']['key']

        ns['other']['new'] = 'value'
        ns.write('new_config.ini')

    """

    #: Name of default section (:attr:`~inirama.Namespace.default`)
    default_section = 'DEFAULT'

    #: Dont raise any exception on file reading errors
    silent_read = True

    #: Class for generating sections
    section_type = Section

    def __init__(self, **default_items):
        self.sections = OrderedDict()
        for k, v in default_items.items():
            self[self.default_section][k] = v

    @property
    def default(self):
        """ Return default section or empty dict.

        :return :class:`inirama.Section`: section

        """
        return self.sections.get(self.default_section, dict())

    def read(self, *files, **params):
        """ Read and parse INI files.

        :param *files: Files for reading
        :param **params: Params for parsing

        Set `update=False` for prevent values redefinition.

        """
        for f in files:
            try:
                with io.open(f, encoding='utf-8') as ff:
                    NS_LOGGER.info('Read from `{0}`'.format(ff.name))
                    self.parse(ff.read(), **params)
            except (IOError, TypeError, SyntaxError, io.UnsupportedOperation):
                if not self.silent_read:
                    NS_LOGGER.error('Reading error `{0}`'.format(ff.name))
                    raise

    def write(self, f):
        """ Write namespace as INI file.

        :param f: File object or path to file.

        """
        if isinstance(f, str):
            f = io.open(f, 'w', encoding='utf-8')

        if not hasattr(f, 'read'):
            raise AttributeError("Wrong type of file: {0}".format(type(f)))

        NS_LOGGER.info('Write to `{0}`'.format(f.name))
        for section in self.sections.keys():
            f.write('[{0}]\n'.format(section))
            for k, v in self[section].items():
                f.write('{0:15}= {1}\n'.format(k, v))
            f.write('\n')
        f.close()

    def parse(self, source, update=True, **params):
        """ Parse INI source as string.

        :param source: Source of INI
        :param update: Replace already defined items

        """
        scanner = INIScanner(source)
        scanner.scan()

        section = self.default_section
        name = None

        for token in scanner.tokens:
            if token[0] == 'KEY_VALUE':
                name, value = re.split('[=:]', token[1], 1)
                name, value = name.strip(), value.strip()
                if not update and name in self[section]:
                    continue
                self[section][name] = value

            elif token[0] == 'SECTION':
                section = token[1].strip('[]')

            elif token[0] == 'CONTINUATION':
                if not name:
                    raise SyntaxError(
                        "SyntaxError[@char {0}: {1}]".format(
                            token[2], "Bad continuation."))
                self[section][name] += '\n' + token[1].strip()

    def __getitem__(self, name):
        """ Look name in self sections.

        :return :class:`inirama.Section`: section

        """
        if name not in self.sections:
            self.sections[name] = self.section_type(self)
        return self.sections[name]

    def __contains__(self, name):
        return name in self.sections

    def __repr__(self):
        return "<Namespace: {0}>".format(self.sections)


class InterpolationNamespace(Namespace):

    """ That implements the interpolation feature.

    ::

        from inirama import InterpolationNamespace

        ns = InterpolationNamespace()
        ns.parse('''
            [main]
            test = value
            foo = bar {test}
            more_deep = wow {foo}
        ''')
        print ns['main']['more_deep']  # wow bar value

    """

    section_type = InterpolationSection

# pylama:ignore=D,W02,E731,W0621
