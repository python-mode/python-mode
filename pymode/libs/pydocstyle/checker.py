"""Parsed source code checkers for docstring violations."""

import ast
import string
import sys
import tokenize as tk
from itertools import takewhile
from re import compile as re

from . import violations
from .config import IllegalConfiguration
# TODO: handle
from .parser import *
from .utils import log, is_blank


__all__ = ('check', )


# If possible (python >= 3.2) use tokenize.open to open files, so PEP 263
# encoding markers are interpreted.
try:
    tokenize_open = tk.open
except AttributeError:
    tokenize_open = open


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
                    if definition.skipped_error_codes != 'all':
                        error = check(None, definition, definition.docstring)
                    else:
                        error = None
                    errors = error if hasattr(error, '__iter__') else [error]
                    for error in errors:
                        if error is not None and error.code not in \
                                definition.skipped_error_codes:
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
            codes = {Module: violations.D100,
                     Class: violations.D101,
                     NestedClass: violations.D101,
                     Method: (lambda: violations.D105() if definition.is_magic
                              else violations.D102()),
                     Function: violations.D103,
                     NestedFunction: violations.D103,
                     Package: violations.D104}
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
                    return violations.D200(len(lines))

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
                yield violations.D201(blanks_before_count)
            if not all(blanks_after) and blanks_after_count != 0:
                yield violations.D202(blanks_after_count)

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
                yield violations.D211(blanks_before_count)
            if blanks_before_count != 1:
                yield violations.D203(blanks_before_count)
            if not all(blanks_after) and blanks_after_count != 1:
                yield violations.D204(blanks_after_count)

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
                    return violations.D205(blanks_count)

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
                    yield violations.D206()
                if (len(indents) > 1 and min(indents[:-1]) > indent or
                        indents[-1] > indent):
                    yield violations.D208()
                if min(indents) < indent:
                    yield violations.D207()

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
                    return violations.D209()

    @check_for(Definition)
    def check_surrounding_whitespaces(self, definition, docstring):
        """D210: No whitespaces allowed surrounding docstring text."""
        if docstring:
            lines = ast.literal_eval(docstring).split('\n')
            if lines[0].startswith(' ') or \
                    len(lines) == 1 and lines[0].endswith(' '):
                return violations.D210()

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
                    return violations.D212()
                else:
                    return violations.D213()

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
                return violations.D300(quotes)

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
            return violations.D301()

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
                return violations.D302()

    @check_for(Definition)
    def check_ends_with_period(self, definition, docstring):
        """D400: First line should end with a period.

        The [first line of a] docstring is a phrase ending in a period.

        """
        if docstring:
            summary_line = ast.literal_eval(docstring).strip().split('\n')[0]
            if not summary_line.endswith('.'):
                return violations.D400(summary_line[-1])

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
                    return violations.D401(first_word[:-1], first_word)

    @check_for(Function)
    def check_no_signature(self, function, docstring):  # def context
        """D402: First line should not be function's or method's "signature".

        The one-line docstring should NOT be a "signature" reiterating the
        function/method parameters (which can be obtained by introspection).

        """
        if docstring:
            first_line = ast.literal_eval(docstring).strip().split('\n')[0]
            if function.name + '(' in first_line.replace(' ', ''):
                return violations.D402()

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
                return violations.D403(first_word.capitalize(), first_word)

    @check_for(Definition)
    def check_starts_with_this(self, function, docstring):
        """D404: First word of the docstring should not be `This`.

        Docstrings should use short, simple language. They should not begin
        with "This class is [..]" or "This module contains [..]".

        """
        if docstring:
            first_word = ast.literal_eval(docstring).split()[0]
            if first_word.lower() == 'this':
                return violations.D404()


parse = Parser()


def check(filenames, select=None, ignore=None):
    """Generate docstring errors that exist in `filenames` iterable.

    By default, the PEP-257 convention is checked. To specifically define the
    set of error codes to check for, supply either `select` or `ignore` (but
    not both). In either case, the parameter should be a collection of error
    code strings, e.g., {'D100', 'D404'}.

    When supplying `select`, only specified error codes will be reported.
    When supplying `ignore`, all error codes which were not specified will be
    reported.

    Note that ignored error code refer to the entire set of possible
    error codes, which is larger than just the PEP-257 convention. To your
    convenience, you may use `pydocstyle.violations.conventions.pep257` as
    a base set to add or remove errors from.

    Examples
    ---------
    >>> check(['pydocstyle.py'])
    <generator object check at 0x...>

    >>> check(['pydocstyle.py'], select=['D100'])
    <generator object check at 0x...>

    >>> check(['pydocstyle.py'], ignore=conventions.pep257 - {'D100'})
    <generator object check at 0x...>

    """
    if select is not None and ignore is not None:
        raise IllegalConfiguration('Cannot pass both select and ignore. '
                                   'They are mutually exclusive.')
    elif select is not None:
        checked_codes = select
    elif ignore is not None:
        checked_codes = list(set(violations.ErrorRegistry.get_error_codes()) -
                             set(ignore))
    else:
        checked_codes = violations.conventions.pep257

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


def is_ascii(string):
    return all(ord(char) < 128 for char in string)


def leading_space(string):
    return re('\s*').match(string).group()
