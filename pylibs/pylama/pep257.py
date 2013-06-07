#! /usr/bin/env python
"""Static analysis tool for checking docstring conventions and style.

About
-----

Currently implemented checks cover most of PEP257:
http://www.python.org/dev/peps/pep-0257/

After PEP257 is covered and tested, other checks might be added,
e.g. NumPy docstring conventions is the first candidate:
https://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt

The main repository of this program is located at:
http://github.com/GreenSteam/pep257

Creating own checks
-------------------

In order to add your own check, create a function in "Checks functions"
section below. The function should take 3 parameters:

docstring : str
    Docstring to check, as it is in file (with quotes).
context : str
    Docstring's context (e.g. function's source code).
is_script : bool
    Whether the docstring is script with #! or not.

Depending on 1st parameter name, the function will be called with
different type of docstring:

 * module_docstring
 * function_docstring
 * class_docstring
 * method_docstring
 * def_docstring (i.e. function-docstrings + method-docstrings)
 * docstring (i.e. all above docstring types)

E.g. the following function will be fed only class-docstrings:

    def your_check(class_docstring, context, is_script):
        pass

If for a certain function, class, etc. a docstring does not exist,
then `None` will be passed, which should be taken into account.

To signify that a check passed successfully simply `return` from the
check function.  If a check failed, return `True`.  If a check failed
and you can provide the precise position where it failed, return a
tuple (start_position, end_position), where start and end positions
are integers specifying where in `context` the failure occured.

Also, see examples in "Check functions" section.

"""

from curses.ascii import isascii
import inspect
from optparse import OptionParser
from os import walk
from os.path import abspath, basename, expanduser, isdir, isfile
from os.path import join as path_join
import re
import sys
import tokenize as tk


try:
    from StringIO import StringIO
except ImportError:
    # Python 3.0 and later
    from io import StringIO


try:
    all
    any
except NameError:
    # Python 2.4 and earlier
    def all(iterable):
        for element in iterable:
            if not element:
                return False
        return True

    def any(iterable):
        for element in iterable:
            if element:
                return True
        return False


try:
    next
except NameError:
    # Python 2.5 and earlier
    def next(obj):
        return obj.next()


#
# Helper functions
#

def cached(f):
    """A decorator that caches function results.

    No cache expiration is currently done.

    """
    cache = {}

    def cached_func(*args, **kwargs):
        key = (args, tuple(kwargs.items()))
        if key in cache:
            return cache[key]
        else:
            res = f(*args, **kwargs)
            cache[key] = res
            return res
    return cached_func


def yield_list(f):
    """Convert generator into list-returning function (decorator)."""
    return lambda *arg, **kw: list(f(*arg, **kw))


def remove_comments(s):
    return re.sub('#[^\n]', '', s)


def abs_pos(marker, source):
    """Return absolute position in source given (line, character) marker."""
    line, char = marker
    lines = StringIO(source).readlines()
    return len(''.join(lines[:line - 1])) + char


def rel_pos(abs_pos, source):
    """Given absolute position, return relative (line, character) in source."""
    lines = StringIO(source).readlines()
    nchars = len(source)
    assert nchars >= abs_pos
    while nchars > abs_pos:
        assert nchars >= abs_pos
        nchars -= len(lines[-1])
        lines.pop()
    return len(lines) + 1, abs_pos - len(''.join(lines))


#
# Parsing
#


def parse_module_docstring(source):
    for kind, value, _, _, _ in tk.generate_tokens(StringIO(source).readline):
        if kind in [tk.COMMENT, tk.NEWLINE, tk.NL]:
            continue
        elif kind == tk.STRING:  # first STRING should be docstring
            return value
        else:
            return None


def parse_docstring(source, what=''):
    """Parse docstring given `def` or `class` source."""
    if what.startswith('module'):
        return parse_module_docstring(source)
    token_gen = tk.generate_tokens(StringIO(source).readline)
    try:
        kind = None
        while kind != tk.INDENT:
            kind, _, _, _, _ = next(token_gen)
        kind, value, _, _, _ = next(token_gen)
        if kind == tk.STRING:  # STRING after INDENT is a docstring
            return value
    except StopIteration:
        pass


@yield_list
def parse_top_level(source, keyword):
    """Parse top-level functions or classes."""
    token_gen = tk.generate_tokens(StringIO(source).readline)
    kind, value, char = None, None, None
    while True:
        start, end = None, None
        while not (kind == tk.NAME and value == keyword and char == 0):
            kind, value, (line, char), _, _ = next(token_gen)
        start = line, char
        while not (kind == tk.DEDENT and value == '' and char == 0):
            kind, value, (line, char), _, _ = next(token_gen)
        end = line, char
        yield source[abs_pos(start, source): abs_pos(end, source)]


@cached
def parse_functions(source):
    return parse_top_level(source, 'def')


@cached
def parse_classes(source):
    return parse_top_level(source, 'class')


def skip_indented_block(token_gen):
    kind, value, start, end, raw = next(token_gen)
    while kind != tk.INDENT:
        kind, value, start, end, raw = next(token_gen)
    indent = 1
    for kind, value, start, end, raw in token_gen:
        if kind == tk.INDENT:
            indent += 1
        elif kind == tk.DEDENT:
            indent -= 1
        if indent == 0:
            return kind, value, start, end, raw


@cached
@yield_list
def parse_methods(source):
    source = ''.join(parse_classes(source))
    token_gen = tk.generate_tokens(StringIO(source).readline)
    kind, value, char = None, None, None
    while True:
        start, end = None, None
        while not (kind == tk.NAME and value == 'def'):
            kind, value, (line, char), _, _ = next(token_gen)
        start = line, char
        kind, value, (line, char), _, _ = skip_indented_block(token_gen)
        end = line, char
        yield source[abs_pos(start, source): abs_pos(end, source)]


def parse_contexts(source, kind):
    if kind == 'module_docstring':
        return [source]
    if kind == 'function_docstring':
        return parse_functions(source)
    if kind == 'class_docstring':
        return parse_classes(source)
    if kind == 'method_docstring':
        return parse_methods(source)
    if kind == 'def_docstring':
        return parse_functions(source) + parse_methods(source)
    if kind == 'docstring':
        return ([source] + parse_functions(source) +
                parse_classes(source) + parse_methods(source))


#
# Framework
#


class Error(object):

    """Error in docstring style.

    * Stores relevant data about the error,
    * provides format for printing an error,
    * provides __lt__ method to sort errors.

    """

    # options that define how errors are printed
    explain = False
    range = False
    quote = False

    def __init__(self, filename, source, docstring, context,
                 explanation, start=None, end=None):
        self.filename = filename
        self.source = source
        self.docstring = docstring
        self.context = context
        self.explanation = explanation.strip()

        if start is None:
            self.start = source.find(context) + context.find(docstring)
        else:
            self.start = source.find(context) + start
        self.line, self.char = rel_pos(self.start, self.source)

        if end is None:
            self.end = self.start + len(docstring)
        else:
            self.end = source.find(context) + end
        self.end_line, self.end_char = rel_pos(self.end, self.source)

    def __str__(self):
        s = self.filename + ':%d:%d' % (self.line, self.char)
        if self.range:
            s += '..%d:%d' % (self.end_line, self.end_char)
        if self.explain:
            s += ': ' + self.explanation + '\n'
        else:
            s += ': ' + self.explanation.split('\n')[0].strip()
        if self.quote:
            quote = self.source[self.start:self.end].strip()
            s += '\n>     ' + '\n> '.join(quote.split('\n')) + '\n'
        return s

    def __lt__(self, other):
        return (self.filename, self.start) < (other.filename, other.start)


@yield_list
def find_checks(keyword):
    for function in globals().values():
        if inspect.isfunction(function):
            args = inspect.getargspec(function)[0]
            if args and args[0] == keyword:
                yield function


@yield_list
def check_source(source, filename):
    keywords = ['module_docstring', 'function_docstring',
                'class_docstring', 'method_docstring',
                'def_docstring', 'docstring']  # TODO? 'nested_docstring']
    is_script = source.startswith('#!') or \
        basename(filename).startswith('test_')
    for keyword in keywords:
        for check in find_checks(keyword):
            for context in parse_contexts(source, keyword):
                docstring = parse_docstring(context, keyword)
                result = check(docstring, context, is_script)
                if result:
                    positions = [] if result is True else result
                    yield Error(filename, source, docstring, context,
                                check.__doc__, *positions)


def find_input_files(filenames):
    """ Return a list of input files.

    `filenames` is a list of filenames, which may be either files
    or directories.  Files within subdirectories are added
    recursively.

    """
    input_files = []

    filenames = [abspath(expanduser(f)) for f in filenames]
    for filename in filenames:
        if isdir(filename):
            for root, _dirs, files in walk(filename):
                input_files += [path_join(root, f) for f in sorted(files)
                                if f.endswith(".py")]
        elif isfile(filename):
            input_files += [filename]
        else:
            print_error("%s is not a file or directory" % filename)

    return input_files


def check_files(filenames):
    r"""Return list of docstring style errors found in files.

    Example
    -------
    >>> import pep257
    >>> pep257.check_files(['one.py', 'two.py'])
    ['one.py:23:1 PEP257 Use u\"\"\" for Unicode docstrings.']

    """
    errors = []
    for filename in find_input_files(filenames):
        errors.extend(check_source(open(filename).read(), filename))
    return [str(e) for e in errors]


def parse_options():
    parser = OptionParser()
    parser.add_option('-e', '--explain', action='store_true',
                      help='show explanation of each error')
    parser.add_option('-r', '--range', action='store_true',
                      help='show error start..end positions')
    parser.add_option('-q', '--quote', action='store_true',
                      help='quote erroneous lines')
    return parser.parse_args()


def print_error(message):
    sys.stderr.write(message)
    sys.stderr.write('\n')
    sys.stderr.flush()


def main(options, arguments):
    print('=' * 80)
    print('Note: checks are relaxed for scripts (with #!) compared to modules')
    Error.explain = options.explain
    Error.range = options.range
    Error.quote = options.quote
    errors = []

    for filename in find_input_files(arguments):
        try:
            f = open(filename)
        except IOError:
            print_error("Error opening file %s" % filename)
        else:
            try:
                errors.extend(check_source(f.read(), filename))
            except IOError:
                print_error("Error reading file %s" % filename)
            except tk.TokenError:
                print_error("Error parsing file %s" % filename)
            finally:
                f.close()
    for error in sorted(errors):
        print_error(str(error))


#
# Check functions
#


def check_modules_have_docstrings(module_docstring, context, is_script):
    """All modules should have docstrings.

    All modules should normally have docstrings.

    """
    if not module_docstring:  # or not eval(module_docstring).strip():
        return 0, min(79, len(context))
    if not eval(module_docstring).strip():
        return True


def check_def_has_docstring(def_docstring, context, is_script):
    """Exported definitions should have docstrings.

    ...all functions and classes exported by a module should also have
    docstrings. Public methods (including the __init__ constructor)
    should also have docstrings.

    """
    if is_script:
        return  # assume nothing is exported
    def_name = context.split()[1]
    if def_name.startswith('_') and not def_name.endswith('__'):
        return  # private, not exported
    if not def_docstring:
        return 0, len(context.split('\n')[0])
    if not eval(def_docstring).strip():
        return True


def check_class_has_docstring(class_docstring, context, is_script):
    """Exported classes should have docstrings.

    ...all functions and classes exported by a module should also have
    docstrings.

    """
    if is_script:
        return  # assume nothing is exported
    class_name = context.split()[1]
    if class_name.startswith('_'):
        return  # not exported
    if not class_docstring:
        return 0, len(context.split('\n')[0])
    if not eval(class_docstring).strip():
        return True


def check_triple_double_quotes(docstring, context, is_script):
    r"""Use \"\"\"triple double quotes\"\"\".

    For consistency, always use \"\"\"triple double quotes\"\"\" around
    docstrings. Use r\"\"\"raw triple double quotes\"\"\" if you use any
    backslashes in your docstrings. For Unicode docstrings, use
    u\"\"\"Unicode triple-quoted strings\"\"\".

    """
    if docstring and not (docstring.startswith('"""') or
                          docstring.startswith('r"""') or
                          docstring.startswith('u"""')):
        return True


def check_backslashes(docstring, context, is_script):
    r"""Use r\"\"\" if any backslashes in your docstrings.

    Use r\"\"\"raw triple double quotes\"\"\" if you use any backslashes
    (\\) in your docstrings.

    """
    if docstring and "\\" in docstring and not docstring.startswith('r"""'):
        return True


def check_unicode_docstring(docstring, context, is_script):
    r"""Use u\"\"\" for Unicode docstrings.

    For Unicode docstrings, use u\"\"\"Unicode triple-quoted stringsr\"\"\".

    """
    if (docstring and not all(isascii(char) for char in docstring) and
            not docstring.startswith('u"""')):
        return True


def check_one_liners(docstring, context, is_script):
    """One-liner docstrings should fit on one line with quotes.

    The closing quotes are on the same line as the opening quotes.
    This looks better for one-liners.

    """
    if not docstring:
        return
    lines = docstring.split('\n')
    if len(lines) > 1:
        non_empty = [l for l in lines if any([c.isalpha() for c in l])]
        if len(non_empty) == 1:
            return True


def check_no_blank_before(def_docstring, context, is_script):
    """No blank line before docstring in definitions.

    There's no blank line either before or after the docstring.

    """
    if not def_docstring:
        return
    before = remove_comments(context.split(def_docstring)[0])
    if before.split(':')[-1].count('\n') > 1:
        return True


def check_ends_with_period(docstring, context, is_script):
    """First line should end with a period.

    The [first line of a] docstring is a phrase ending in a period.

    """
    if docstring and not eval(docstring).split('\n')[0].strip().endswith('.'):
        return True


def check_imperative_mood(def_docstring, context, is_script):
    """First line should be in imperative mood ('Do', not 'Does').

    [Docstring] prescribes the function or method's effect as a command:
    ("Do this", "Return that"), not as a description; e.g. don't write
    "Returns the pathname ...".

    """
    if def_docstring and eval(def_docstring).strip():
        first_word = eval(def_docstring).strip().split()[0]
        if first_word.endswith('s') and not first_word.endswith('ss'):
            return True


def check_no_signature(def_docstring, context, is_script):
    """First line should not be function's or method's "signature".

    The one-line docstring should NOT be a "signature" reiterating
    the function/method parameters (which can be obtained by introspection).

    """
    if not def_docstring:
        return
    def_name = context.split(def_docstring)[0].split()[1].split('(')[0]
    first_line = eval(def_docstring).split('\n')[0]
    if def_name + '(' in first_line.replace(' ', ''):
        return True


def check_return_type(def_docstring, context, is_script):
    """Return value type should be mentioned.

    However, the nature of the return value cannot be determined by
    introspection, so it should be mentioned.

    """
    if (not def_docstring) or is_script:
        return
    if 'return' not in def_docstring.lower():
        tokens = list(tk.generate_tokens(StringIO(context).readline))
        after_return = [tokens[i + 1][0] for i, token in enumerate(tokens)
                        if token[1] == 'return']
        # not very precise (tk.OP ';' is not taken into account)
        if set(after_return) - set([tk.COMMENT, tk.NL, tk.NEWLINE]) != set([]):
            return True


def check_blank_after_summary(docstring, context, is_script):
    """Blank line missing after one-line summary.

    Multi-line docstrings consist of a summary line just like a one-line
    docstring, followed by a blank line, followed by a more elaborate
    description. The summary line may be used by automatic indexing tools;
    it is important that it fits on one line and is separated from the
    rest of the docstring by a blank line.

    """
    if not docstring:
        return
    lines = eval(docstring).split('\n')
    if len(lines) > 1 and lines[1].strip() != '':
        return True


def check_indent(docstring, context, is_script):
    """The entire docstring should be indented same as code.

    The entire docstring is indented the same as the quotes at its
    first line.

    """
    if (not docstring) or len(eval(docstring).split('\n')) == 1:
        return
    non_empty_lines = [line for line in eval(docstring).split('\n')[1:]
                       if line.strip()]
    if not non_empty_lines:
        return
    indent = min([len(l) - len(l.lstrip()) for l in non_empty_lines])
    if indent != len(context.split(docstring)[0].split('\n')[-1]):
        return True


def check_blank_before_after_class(class_docstring, context, is_script):
    """Class docstring should have 1 blank line around them.

    Insert a blank line before and after all docstrings (one-line or
    multi-line) that document a class -- generally speaking, the class's
    methods are separated from each other by a single blank line, and the
    docstring needs to be offset from the first method by a blank line;
    for symmetry, put a blank line between the class header and the
    docstring.

    """
    if not class_docstring:
        return
    before, after = context.split(class_docstring)
    before_blanks = [not line.strip() for line in before.split('\n')]
    after_blanks = [not line.strip() for line in after.split('\n')]
    if before_blanks[-3:] != [False, True, True]:
        return True
    if not all(after_blanks) and after_blanks[:3] != [True, True, False]:
        return True


def check_blank_after_last_paragraph(docstring, context, is_script):
    """Multiline docstring should end with 1 blank line.

    The BDFL recommends inserting a blank line between the last
    paragraph in a multi-line docstring and its closing quotes,
    placing the closing quotes on a line by themselves.

    """
    if (not docstring) or len(eval(docstring).split('\n')) == 1:
        return
    blanks = [not line.strip() for line in eval(docstring).split('\n')]
    if blanks[-3:] != [False, True, True]:
        return True


if __name__ == '__main__':
    try:
        main(*parse_options())
    except KeyboardInterrupt:
        pass
