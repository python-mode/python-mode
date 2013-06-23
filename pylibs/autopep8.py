#!/usr/bin/env python
#
# Copyright (C) 2010-2011 Hideo Hattori
# Copyright (C) 2011-2013 Hideo Hattori, Steven Myint
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""Automatically formats Python code to conform to the PEP 8 style guide.

Fixes that only need be done once can be added by adding a function of the form
"fix_<code>(source)" to this module. They should return the fixed source code.
These fixes are picked up by apply_global_fixes().

Fixes that depend on pep8 should be added as methods to FixPEP8. See the class
documentation for more information.

"""

from __future__ import print_function
from __future__ import division

import codecs
import copy
import fnmatch
import inspect
import os
import re
import signal
import sys
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
import token
import tokenize
from optparse import OptionParser
import difflib
import tempfile

from pylama.checkers import pep8


try:
    unicode
except NameError:
    unicode = str


__version__ = '0.9'


CR = '\r'
LF = '\n'
CRLF = '\r\n'


PYTHON_SHEBANG_REGEX = re.compile(r'^#!.*\bpython[23]?\b')


# For generating line shortening candidates.
SHORTEN_OPERATOR_GROUPS = frozenset([
    frozenset([',']),
    frozenset(['%']),
    frozenset([',', '(', '[', '{']),
    frozenset([',', '(', '[', '{', '%', '+', '-', '*', '/', '//']),
])


DEFAULT_IGNORE = 'E24,W6'


def open_with_encoding(filename, encoding=None, mode='r'):
    """Return opened file with a specific encoding."""
    if not encoding:
        encoding = detect_encoding(filename)

    import io
    return io.open(filename, mode=mode, encoding=encoding,
                   newline='')  # Preserve line endings


def detect_encoding(filename):
    """Return file encoding."""
    try:
        with open(filename, 'rb') as input_file:
            from lib2to3.pgen2 import tokenize as lib2to3_tokenize
            encoding = lib2to3_tokenize.detect_encoding(input_file.readline)[0]

        # Check for correctness of encoding
        with open_with_encoding(filename, encoding) as test_file:
            test_file.read()

        return encoding
    except (SyntaxError, LookupError, UnicodeDecodeError):
        return 'latin-1'


def read_from_filename(filename, readlines=False):
    """Return contents of file."""
    with open_with_encoding(filename) as input_file:
        return input_file.readlines() if readlines else input_file.read()


def extended_blank_lines(logical_line,
                         blank_lines,
                         indent_level,
                         previous_logical):
    """Check for missing blank lines after class declaration."""
    if (previous_logical.startswith('class ')):
        if (logical_line.startswith(('def ', 'class ', '@')) or
                pep8.DOCSTRING_REGEX.match(logical_line)):
            if indent_level:
                if not blank_lines:
                    yield (0, 'E301 expected 1 blank line, found 0')
    elif previous_logical.startswith('def '):
        if blank_lines and pep8.DOCSTRING_REGEX.match(logical_line):
            yield (0, 'E303 too many blank lines ({0})'.format(blank_lines))
pep8.register_check(extended_blank_lines)


class FixPEP8(object):

    """Fix invalid code.

    Fixer methods are prefixed "fix_". The _fix_source() method looks for these
    automatically.

    The fixer method can take either one or two arguments (in addition to
    self). The first argument is "result", which is the error information from
    pep8. The second argument, "logical", is required only for logical-line
    fixes.

    The fixer method can return the list of modified lines or None. An empty
    list would mean that no changes were made. None would mean that only the
    line reported in the pep8 error was modified. Note that the modified line
    numbers that are returned are indexed at 1. This typically would correspond
    with the line number reported in the pep8 error information.

    [fixed method list]
        - e111
        - e121,e122,e123,e124,e125,e126,e127,e128,e129
        - e201,e202,e203
        - e211
        - e221,e222,e223,e224,e225
        - e231
        - e251
        - e261,e262
        - e271,e272,e273,e274
        - e301,e302,e303
        - e401
        - e502
        - e701,e702
        - e711
        - w291,w293
        - w391

    """

    def __init__(self, filename, options, contents=None):
        self.filename = filename
        if contents is None:
            self.source = read_from_filename(filename, readlines=True)
        else:
            sio = StringIO(contents)
            self.source = sio.readlines()
        self.newline = find_newline(self.source)
        self.options = options
        self.indent_word = _get_indentword(unicode().join(self.source))

        # method definition
        self.fix_e111 = self.fix_e101
        self.fix_e128 = self.fix_e127
        self.fix_e129 = self.fix_e125
        self.fix_e202 = self.fix_e201
        self.fix_e203 = self.fix_e201
        self.fix_e211 = self.fix_e201
        self.fix_e221 = self.fix_e271
        self.fix_e222 = self.fix_e271
        self.fix_e223 = self.fix_e271
        self.fix_e226 = self.fix_e225
        self.fix_e227 = self.fix_e225
        self.fix_e228 = self.fix_e225
        self.fix_e241 = self.fix_e271
        self.fix_e242 = self.fix_e224
        self.fix_e261 = self.fix_e262
        self.fix_e272 = self.fix_e271
        self.fix_e273 = self.fix_e271
        self.fix_e274 = self.fix_e271
        self.fix_e703 = self.fix_e702
        self.fix_w191 = self.fix_e101

    def _fix_source(self, results):
        completed_lines = set()
        for result in sorted(results, key=_priority_key):
            if result['line'] in completed_lines:
                continue

            fixed_methodname = 'fix_%s' % result['id'].lower()
            if hasattr(self, fixed_methodname):
                fix = getattr(self, fixed_methodname)

                is_logical_fix = len(inspect.getargspec(fix).args) > 2
                if is_logical_fix:
                    # Do not run logical fix if any lines have been modified.
                    if completed_lines:
                        continue

                    logical = self._get_logical(result)
                    if not logical:
                        continue

                    modified_lines = fix(result, logical)
                else:
                    modified_lines = fix(result)

                if modified_lines:
                    completed_lines.update(modified_lines)
                elif modified_lines == []:  # Empty list means no fix
                    if self.options.verbose >= 2:
                        print(
                            '--->  Not fixing {f} on line {l}'.format(
                                f=result['id'], l=result['line']),
                            file=sys.stderr)
                else:  # We assume one-line fix when None
                    completed_lines.add(result['line'])
            else:
                if self.options.verbose >= 3:
                    print("--->  '%s' is not defined." % fixed_methodname,
                          file=sys.stderr)
                    info = result['info'].strip()
                    print('--->  %s:%s:%s:%s' % (self.filename,
                                                 result['line'],
                                                 result['column'],
                                                 info),
                          file=sys.stderr)

    def fix(self):
        """Return a version of the source code with PEP 8 violations fixed."""
        pep8_options = {
            'ignore': self.options.ignore,
            'select': self.options.select,
            'max_line_length': self.options.max_line_length,
        }
        results = _execute_pep8(pep8_options, self.source)

        if self.options.verbose:
            progress = {}
            for r in results:
                if r['id'] not in progress:
                    progress[r['id']] = set()
                progress[r['id']].add(r['line'])
            print('--->  {n} issue(s) to fix {progress}'.format(
                n=len(results), progress=progress), file=sys.stderr)

        self._fix_source(filter_results(source=unicode().join(self.source),
                                        results=results,
                                        aggressive=self.options.aggressive))
        return unicode().join(self.source)

    def fix_e101(self, _):
        """Reindent all lines."""
        reindenter = Reindenter(self.source, self.newline)
        modified_line_numbers = reindenter.run()
        if modified_line_numbers:
            self.source = reindenter.fixed_lines()
            return modified_line_numbers
        else:
            return []

    def _find_logical(self):
        # make a variable which is the index of all the starts of lines
        logical_start = []
        logical_end = []
        last_newline = True
        sio = StringIO(''.join(self.source))
        parens = 0
        for t in tokenize.generate_tokens(sio.readline):
            if t[0] in [tokenize.COMMENT, tokenize.DEDENT,
                        tokenize.INDENT, tokenize.NL,
                        tokenize.ENDMARKER]:
                continue
            if not parens and t[0] in [
                tokenize.NEWLINE, tokenize.SEMI
            ]:
                last_newline = True
                logical_end.append((t[3][0] - 1, t[2][1]))
                continue
            if last_newline and not parens:
                logical_start.append((t[2][0] - 1, t[2][1]))
                last_newline = False
            if t[0] == tokenize.OP:
                if t[1] in '([{':
                    parens += 1
                elif t[1] in '}])':
                    parens -= 1
        return (logical_start, logical_end)

    def _get_logical(self, result):
        """Return the logical line corresponding to the result.

        Assumes input is already E702-clean.

        """
        try:
            (logical_start, logical_end) = self._find_logical()
        except (IndentationError, tokenize.TokenError):
            return None

        row = result['line'] - 1
        col = result['column'] - 1
        ls = None
        le = None
        for i in range(0, len(logical_start), 1):
            x = logical_end[i]
            if x[0] > row or (x[0] == row and x[1] > col):
                le = x
                ls = logical_start[i]
                break
        if ls is None:
            return None
        original = self.source[ls[0]:le[0] + 1]
        return ls, le, original

    def _fix_reindent(self, result, logical):
        """Fix a badly indented line.

        This is done by adding or removing from its initial indent only.

        """
        assert logical
        ls, _, original = logical

        rewrapper = Wrapper(original)
        valid_indents = rewrapper.pep8_expected()
        if not rewrapper.rel_indent:
            return []  # pragma: no cover
        if result['line'] > ls[0]:
            # got a valid continuation line number from pep8
            row = result['line'] - ls[0] - 1
            # always pick the first option for this
            valid = valid_indents[row]
            got = rewrapper.rel_indent[row]
        else:
            return []  # pragma: no cover
        line = ls[0] + row
        # always pick the expected indent, for now.
        indent_to = valid[0]

        if got != indent_to:
            orig_line = self.source[line]
            new_line = ' ' * (indent_to) + orig_line.lstrip()
            if new_line == orig_line:
                return []
            else:
                self.source[line] = new_line
                return [line + 1]  # Line indexed at 1
        else:
            return []  # pragma: no cover

    def fix_e121(self, result, logical):
        """Fix indentation to be a multiple of four."""
        # Fix by adjusting initial indent level.
        return self._fix_reindent(result, logical)

    def fix_e122(self, result, logical):
        """Add absent indentation for hanging indentation."""
        # Fix by adding an initial indent.
        return self._fix_reindent(result, logical)

    def fix_e123(self, result, logical):
        """Align closing bracket to match opening bracket."""
        # Fix by deleting whitespace to the correct level.
        assert logical
        logical_lines = logical[2]
        line_index = result['line'] - 1
        original_line = self.source[line_index]

        fixed_line = (_get_indentation(logical_lines[0]) +
                      original_line.lstrip())
        if fixed_line == original_line:
            # Fall back to slower method.
            return self._fix_reindent(result, logical)
        else:
            self.source[line_index] = fixed_line

    def fix_e124(self, result, logical):
        """Align closing bracket to match visual indentation."""
        # Fix by inserting whitespace before the closing bracket.
        return self._fix_reindent(result, logical)

    def fix_e125(self, result, logical):
        """Indent to distinguish line from next logical line."""
        # Fix by indenting the line in error to the next stop.
        modified_lines = self._fix_reindent(result, logical)
        if modified_lines:
            return modified_lines
        else:
            # Fallback
            line_index = result['line'] - 1
            original_line = self.source[line_index]
            self.source[line_index] = self.indent_word + original_line

    def fix_e126(self, result, logical):
        """Fix over-indented hanging indentation."""
        # fix by deleting whitespace to the left
        assert logical
        logical_lines = logical[2]
        line_index = result['line'] - 1
        original = self.source[line_index]

        fixed = (_get_indentation(logical_lines[0]) +
                 self.indent_word + original.lstrip())
        if fixed == original:
            # Fall back to slower method.
            return self._fix_reindent(result, logical)  # pragma: no cover
        else:
            self.source[line_index] = fixed

    def fix_e127(self, result, logical):
        """Fix visual indentation."""
        # Fix by inserting/deleting whitespace to the correct level.
        modified_lines = self._align_visual_indent(result, logical)
        if modified_lines != []:
            return modified_lines
        else:
            # Fall back to slower method.
            return self._fix_reindent(result, logical)

    def _align_visual_indent(self, result, logical):
        """Correct visual indent.

        This includes over (E127) and under (E128) indented lines.

        """
        assert logical
        logical_lines = logical[2]
        line_index = result['line'] - 1
        original = self.source[line_index]
        fixed = original

        if logical_lines[0].rstrip().endswith('\\'):
            fixed = (_get_indentation(logical_lines[0]) +
                     self.indent_word + original.lstrip())
        else:
            start_index = None
            for symbol in '([{':
                if symbol in logical_lines[0]:
                    found_index = logical_lines[0].find(symbol)
                    if start_index is None:
                        start_index = found_index
                    else:
                        start_index = min(start_index, found_index)

            if start_index is not None:
                fixed = start_index * ' ' + original.lstrip()

        if fixed == original:
            return []
        else:
            self.source[line_index] = fixed

    def fix_e201(self, result):
        """Remove extraneous whitespace."""
        line_index = result['line'] - 1
        target = self.source[line_index]
        offset = result['column'] - 1

        # When multiline strings are involved, pep8 reports the error as
        # being at the start of the multiline string, which doesn't work
        # for us.
        if ('"""' in target or
            "'''" in target or
                target.rstrip().endswith('\\')):
            return []

        fixed = fix_whitespace(target,
                               offset=offset,
                               replacement='')

        if fixed == target:
            return []
        else:
            self.source[line_index] = fixed

    def fix_e224(self, result):
        """Remove extraneous whitespace around operator."""
        target = self.source[result['line'] - 1]
        offset = result['column'] - 1
        fixed = target[:offset] + target[offset:].replace('\t', ' ')
        self.source[result['line'] - 1] = fixed

    def fix_e225(self, result):
        """Fix missing whitespace around operator."""
        target = self.source[result['line'] - 1]
        offset = result['column'] - 1
        fixed = target[:offset] + ' ' + target[offset:]

        # Only proceed if non-whitespace characters match.
        # And make sure we don't break the indentation.
        if (fixed.replace(' ', '') == target.replace(' ', '') and
                _get_indentation(fixed) == _get_indentation(target)):
            self.source[result['line'] - 1] = fixed
        else:
            return []

    def fix_e231(self, result):
        """Add missing whitespace."""
        # Optimize for comma case. This will fix all commas in the full source
        # code in one pass.
        if ',' in result['info']:
            original = ''.join(self.source)
            new = refactor(original, ['ws_comma'])
            if original.strip() != new.strip():
                self.source = [new]
                return range(1, 1 + len(original))

        line_index = result['line'] - 1
        target = self.source[line_index]
        offset = result['column']
        fixed = target[:offset] + ' ' + target[offset:]
        self.source[line_index] = fixed

    def fix_e251(self, result):
        """Remove whitespace around parameter '=' sign."""
        line_index = result['line'] - 1
        target = self.source[line_index]

        # This is necessary since pep8 sometimes reports columns that goes
        # past the end of the physical line. This happens in cases like,
        # foo(bar\n=None)
        c = min(result['column'] - 1,
                len(target) - 1)

        if target[c].strip():
            fixed = target
        else:
            fixed = target[:c].rstrip() + target[c:].lstrip()

        # There could be an escaped newline
        #
        #     def foo(a=\
        #             1)
        if (fixed.endswith('=\\\n') or
                fixed.endswith('=\\\r\n') or
                fixed.endswith('=\\\r')):
            self.source[line_index] = fixed.rstrip('\n\r \t\\')
            self.source[line_index + 1] = self.source[line_index + 1].lstrip()
            return [line_index + 1, line_index + 2]  # Line indexed at 1

        self.source[result['line'] - 1] = fixed

    def fix_e262(self, result):
        """Fix spacing after comment hash."""
        target = self.source[result['line'] - 1]
        offset = result['column']

        code = target[:offset].rstrip(' \t#')
        comment = target[offset:].lstrip(' \t#')

        fixed = code + ('  # ' + comment if comment.strip()
                        else self.newline)

        self.source[result['line'] - 1] = fixed

    def fix_e271(self, result):
        """Fix extraneous whitespace around keywords."""
        line_index = result['line'] - 1
        target = self.source[line_index]
        offset = result['column'] - 1

        # When multiline strings are involved, pep8 reports the error as
        # being at the start of the multiline string, which doesn't work
        # for us.
        if ('"""' in target or
            "'''" in target or
                target.rstrip().endswith('\\')):
            return []

        fixed = fix_whitespace(target,
                               offset=offset,
                               replacement=' ')

        if fixed == target:
            return []
        else:
            self.source[line_index] = fixed

    def fix_e301(self, result):
        """Add missing blank line."""
        cr = self.newline
        self.source[result['line'] - 1] = cr + self.source[result['line'] - 1]

    def fix_e302(self, result):
        """Add missing 2 blank lines."""
        add_linenum = 2 - int(result['info'].split()[-1])
        cr = self.newline * add_linenum
        self.source[result['line'] - 1] = cr + self.source[result['line'] - 1]

    def fix_e303(self, result):
        """Remove extra blank lines."""
        delete_linenum = int(result['info'].split('(')[1].split(')')[0]) - 2
        delete_linenum = max(1, delete_linenum)

        # We need to count because pep8 reports an offset line number if there
        # are comments.
        cnt = 0
        line = result['line'] - 2
        modified_lines = []
        while cnt < delete_linenum and line >= 0:
            if not self.source[line].strip():
                self.source[line] = ''
                modified_lines.append(1 + line)  # Line indexed at 1
                cnt += 1
            line -= 1

        return modified_lines

    def fix_e304(self, result):
        """Remove blank line following function decorator."""
        line = result['line'] - 2
        if not self.source[line].strip():
            self.source[line] = ''

    def fix_e401(self, result):
        """Put imports on separate lines."""
        line_index = result['line'] - 1
        target = self.source[line_index]
        offset = result['column'] - 1

        if not target.lstrip().startswith('import'):
            return []

        # pep8 (1.3.1) reports false positive if there is an import statement
        # followed by a semicolon and some unrelated statement with commas in
        # it.
        if ';' in target:
            return []

        indentation = re.split(pattern=r'\bimport\b',
                               string=target, maxsplit=1)[0]
        fixed = (target[:offset].rstrip('\t ,') + self.newline +
                 indentation + 'import ' + target[offset:].lstrip('\t ,'))
        self.source[line_index] = fixed

    def fix_e501(self, result):
        """Try to make lines fit within --max-line-length characters."""
        line_index = result['line'] - 1
        target = self.source[line_index]

        if target.lstrip().startswith('#'):
            # Shorten comment if it is the last comment line.
            try:
                if self.source[line_index + 1].lstrip().startswith('#'):
                    return []
            except IndexError:
                pass

            # Wrap commented lines.
            fixed = shorten_comment(
                line=target,
                newline=self.newline,
                max_line_length=self.options.max_line_length)
            if fixed == self.source[line_index]:
                return []
            else:
                self.source[line_index] = fixed
                return

        indent = _get_indentation(target)
        source = target[len(indent):]
        assert source.lstrip() == source
        sio = StringIO(source)

        # Check for multiline string.
        try:
            tokens = list(tokenize.generate_tokens(sio.readline))
        except (tokenize.TokenError, IndentationError):
            multiline_candidate = break_multiline(
                target, newline=self.newline,
                indent_word=self.indent_word)

            if multiline_candidate:
                self.source[line_index] = multiline_candidate
                return
            else:
                return []

        candidates = shorten_line(
            tokens, source, indent,
            self.indent_word, newline=self.newline,
            aggressive=self.options.aggressive)

        candidates = list(sorted(
            set(candidates),
            key=lambda x: line_shortening_rank(x,
                                               self.newline,
                                               self.indent_word)))

        if self.options.verbose >= 4:
            print(('-' * 79 + '\n').join([''] + candidates + ['']),
                  file=codecs.getwriter('utf-8')(sys.stderr.buffer
                                                 if hasattr(sys.stderr,
                                                            'buffer')
                                                 else sys.stderr))

        for _candidate in candidates:
            assert _candidate is not None

            if (get_longest_length(_candidate, self.newline) >=
                    get_longest_length(target, self.newline)):
                continue

            self.source[line_index] = _candidate
            return

        return []

    def fix_e502(self, result):
        """Remove extraneous escape of newline."""
        line_index = result['line'] - 1
        target = self.source[line_index]
        self.source[line_index] = target.rstrip('\n\r \t\\') + self.newline

    def fix_e701(self, result):
        """Put colon-separated compound statement on separate lines."""
        line_index = result['line'] - 1
        target = self.source[line_index]
        c = result['column']

        fixed_source = (target[:c] + self.newline +
                        _get_indentation(target) + self.indent_word +
                        target[c:].lstrip('\n\r \t\\'))
        self.source[result['line'] - 1] = fixed_source

    def fix_e702(self, result, logical):
        """Put semicolon-separated compound statement on separate lines."""
        logical_lines = logical[2]

        line_index = result['line'] - 1
        target = self.source[line_index]

        if target.rstrip().endswith('\\'):
            # Normalize '1; \\\n2' into '1; 2'.
            self.source[line_index] = target.rstrip('\n \r\t\\')
            self.source[line_index + 1] = self.source[line_index + 1].lstrip()
            return [line_index + 1, line_index + 2]

        if target.rstrip().endswith(';'):
            self.source[line_index] = target.rstrip('\n \r\t;') + self.newline
            return

        offset = result['column'] - 1
        first = target[:offset].rstrip(';').rstrip()
        second = (_get_indentation(logical_lines[0]) +
                  target[offset:].lstrip(';').lstrip())

        self.source[line_index] = first + self.newline + second

    def fix_e711(self, result):
        """Fix comparison with None."""
        line_index = result['line'] - 1
        target = self.source[line_index]
        offset = result['column'] - 1

        right_offset = offset + 2
        if right_offset >= len(target):
            return []

        left = target[:offset].rstrip()
        center = target[offset:right_offset]
        right = target[right_offset:].lstrip()

        if not right.startswith('None'):
            return []

        if center.strip() == '==':
            new_center = 'is'
        elif center.strip() == '!=':
            new_center = 'is not'
        else:
            return []

        self.source[line_index] = ' '.join([left, new_center, right])

    def fix_e712(self, result):
        """Fix comparison with boolean."""
        line_index = result['line'] - 1
        target = self.source[line_index]
        offset = result['column'] - 1

        right_offset = offset + 2
        if right_offset >= len(target):
            return []

        left = target[:offset].rstrip()
        center = target[offset:right_offset]
        right = target[right_offset:].lstrip()

        # Handle simple cases only.
        new_right = None
        if center.strip() == '==':
            if re.match(r'\bTrue\b', right):
                new_right = re.sub(r'\bTrue\b *', '', right, count=1)
        elif center.strip() == '!=':
            if re.match(r'\bFalse\b', right):
                new_right = re.sub(r'\bFalse\b *', '', right, count=1)

        if new_right is None:
            return []

        if new_right[0].isalnum():
            new_right = ' ' + new_right

        self.source[line_index] = left + new_right

    def fix_w291(self, result):
        """Remove trailing whitespace."""
        fixed_line = self.source[result['line'] - 1].rstrip()
        self.source[result['line'] - 1] = '%s%s' % (fixed_line, self.newline)

    def fix_w293(self, result):
        """Remove trailing whitespace on blank line."""
        assert not self.source[result['line'] - 1].strip()
        self.source[result['line'] - 1] = self.newline

    def fix_w391(self, _):
        """Remove trailing blank lines."""
        blank_count = 0
        for line in reversed(self.source):
            line = line.rstrip()
            if line:
                break
            else:
                blank_count += 1

        original_length = len(self.source)
        self.source = self.source[:original_length - blank_count]
        return range(1, 1 + original_length)


def fix_e26(source):
    """Format block comments."""
    if '#' not in source:
        # Optimization.
        return source

    string_line_numbers = multiline_string_lines(source,
                                                 include_docstrings=True)
    fixed_lines = []
    sio = StringIO(source)
    for (line_number, line) in enumerate(sio.readlines(), start=1):
        if (line.lstrip().startswith('#') and
                line_number not in string_line_numbers):

            indentation = _get_indentation(line)
            line = line.lstrip()

            # Normalize beginning if not a shebang.
            if len(line) > 1:
                # Leave multiple spaces like '#    ' alone.
                if line.count('#') > 1 or line[1].isalnum():
                    line = '# ' + line.lstrip('# \t')

            fixed_lines.append(indentation + line)
        else:
            fixed_lines.append(line)

    return ''.join(fixed_lines)


def refactor(source, fixer_names, ignore=None):
    """Return refactored code using lib2to3.

    Skip if ignore string is produced in the refactored code.

    """
    from lib2to3 import pgen2
    try:
        new_text = refactor_with_2to3(source,
                                      fixer_names=fixer_names)
    except (pgen2.parse.ParseError,
            UnicodeDecodeError,
            UnicodeEncodeError,
            IndentationError):
        return source

    if ignore:
        if ignore in new_text and ignore not in source:
            return source

    return new_text


def fix_w602(source):
    """Fix deprecated form of raising exception."""
    return refactor(source, ['raise'],
                    ignore='with_traceback')


def fix_w6(source):
    """Fix various deprecated code (via lib2to3)."""
    return refactor(source,
                    ['apply',
                     'except',
                     'exec',
                     'execfile',
                     'exitfunc',
                     'has_key',
                     'idioms',
                     'import',
                     'methodattrs',  # Python >= 2.6
                     'ne',
                     'numliterals',
                     'operator',
                     'paren',
                     'reduce',
                     'renames',
                     'repr',
                     'standarderror',
                     'sys_exc',
                     'throw',
                     'tuple_params',
                     'types',
                     'xreadlines'])


def find_newline(source):
    """Return type of newline used in source."""
    cr, lf, crlf = 0, 0, 0
    for s in source:
        if s.endswith(CRLF):
            crlf += 1
        elif s.endswith(CR):
            cr += 1
        elif s.endswith(LF):
            lf += 1
    _max = max(lf, cr, crlf)
    if _max == lf:
        return LF
    elif _max == crlf:
        return CRLF
    else:
        return CR


def _get_indentword(source):
    """Return indentation type."""
    sio = StringIO(source)
    indent_word = '    '  # Default in case source has no indentation
    try:
        for t in tokenize.generate_tokens(sio.readline):
            if t[0] == token.INDENT:
                indent_word = t[1]
                break
    except (tokenize.TokenError, IndentationError):
        pass
    return indent_word


def _get_indentation(line):
    """Return leading whitespace."""
    if line.strip():
        non_whitespace_index = len(line) - len(line.lstrip())
        return line[:non_whitespace_index]
    else:
        return ''


def get_diff_text(old, new, filename):
    """Return text of unified diff between old and new."""
    newline = '\n'
    diff = difflib.unified_diff(
        old, new,
        'original/' + filename,
        'fixed/' + filename,
        lineterm=newline)

    text = ''
    for line in diff:
        text += line

        # Work around missing newline (http://bugs.python.org/issue2142).
        if not line.endswith(newline):
            text += newline + r'\ No newline at end of file' + newline

    return text


def _priority_key(pep8_result):
    """Key for sorting PEP8 results.

    Global fixes should be done first. This is important for things
    like indentation.

    """
    priority = [
        # Global fixes.
        'e101', 'e111', 'w191',
        # Fix multiline colon-based before semicolon based.
        'e701',
        # Break multiline statements early.
        'e702',
        # Things that make lines longer.
        'e225', 'e231',
        # Remove extraneous whitespace before breaking lines.
        'e201',
        # Before breaking lines.
        'e121', 'e122', 'e123', 'e124', 'e125', 'e126', 'e127', 'e128', 'e129',
    ]
    key = pep8_result['id'].lower()
    if key in priority:
        return priority.index(key)
    else:
        # Lowest priority
        return len(priority)


def shorten_line(tokens, source, indentation, indent_word, newline,
                 aggressive=False):
    """Separate line at OPERATOR.

    Multiple candidates will be yielded.

    """
    for candidate in _shorten_line(tokens=tokens,
                                   source=source,
                                   indentation=indentation,
                                   indent_word=indent_word,
                                   newline=newline,
                                   aggressive=aggressive):
        yield candidate

    if aggressive:
        for key_token_strings in SHORTEN_OPERATOR_GROUPS:
            shortened = _shorten_line_at_tokens(
                tokens=tokens,
                source=source,
                indentation=indentation,
                indent_word=indent_word,
                newline=newline,
                key_token_strings=key_token_strings,
                aggressive=aggressive)

            if shortened is not None and shortened != source:
                yield shortened


def _shorten_line(tokens, source, indentation, indent_word, newline,
                  aggressive=False):
    """Separate line at OPERATOR.

    Multiple candidates will be yielded.

    """
    for tkn in tokens:
        # Don't break on '=' after keyword as this violates PEP 8.
        if token.OP == tkn[0] and tkn[1] != '=':
            assert tkn[0] != token.INDENT

            offset = tkn[2][1] + 1
            first = source[:offset]

            second_indent = indentation
            if first.rstrip().endswith('('):
                second_indent += indent_word
            elif '(' in first:
                second_indent += ' ' * (1 + first.find('('))
            else:
                second_indent += indent_word

            second = (second_indent + source[offset:].lstrip())
            if not second.strip():
                continue

            # Do not begin a line with a comma
            if second.lstrip().startswith(','):
                continue
            # Do end a line with a dot
            if first.rstrip().endswith('.'):
                continue
            if tkn[1] in '+-*/':
                fixed = first + ' \\' + newline + second
            else:
                fixed = first + newline + second

            # Only fix if syntax is okay.
            if check_syntax(normalize_multiline(fixed, newline=newline)
                            if aggressive else fixed):
                yield indentation + fixed


def _shorten_line_at_tokens(tokens, source, indentation, indent_word, newline,
                            key_token_strings, aggressive):
    """Separate line by breaking at tokens in key_token_strings.

    This will always break the line at the first parenthesis.

    """
    offsets = []
    first_paren = True
    for tkn in tokens:
        token_type = tkn[0]
        token_string = tkn[1]
        next_offset = tkn[2][1] + 1

        assert token_type != token.INDENT

        if token_string in key_token_strings or (first_paren and
                                                 token_string == '('):
            # Don't split right before newline.
            if next_offset < len(source) - 1:
                offsets.append(next_offset)

            if token_string == '(':
                first_paren = False

    current_indent = None
    fixed = None
    for line in split_at_offsets(source, offsets):
        if fixed:
            fixed += newline + current_indent + line

            for symbol in '([{':
                if line.endswith(symbol):
                    current_indent += indent_word
        else:
            # First line.
            fixed = line
            assert not current_indent
            current_indent = indent_word

    assert fixed is not None

    if check_syntax(normalize_multiline(fixed, newline=newline)
                    if aggressive > 1 else fixed):
        return indentation + fixed
    else:
        return None


def normalize_multiline(line, newline):
    """Remove multiline-related code that will cause syntax error.

    This is for purposes of checking syntax.

    """
    for quote in '\'"':
        dict_pattern = r'^{q}[^{q}]*{q} *: *'.format(q=quote)
        if re.match(dict_pattern, line):
            if not line.strip().endswith('}'):
                line += '}'
            return '{' + line

    if line.startswith('def ') and line.rstrip().endswith(':'):
        # Do not allow ':' to be alone. That is invalid.
        split_line = [item.strip() for item in line.split(newline)]
        if ':' not in split_line and 'def' not in split_line:
            return line[len('def'):].strip().rstrip(':')

    return line


def fix_whitespace(line, offset, replacement):
    """Replace whitespace at offset and return fixed line."""
    # Replace escaped newlines too
    left = line[:offset].rstrip('\n\r \t\\')
    right = line[offset:].lstrip('\n\r \t\\')
    if right.startswith('#'):
        return line
    else:
        return left + replacement + right


def _execute_pep8(pep8_options, source):
    """Execute pep8 via python method calls."""
    class QuietReport(pep8.BaseReport):

        """Version of checker that does not print."""

        def __init__(self, options):
            super(QuietReport, self).__init__(options)
            self.__full_error_results = []

        def error(self, line_number, offset, text, _):
            """Collect errors."""
            code = super(QuietReport, self).error(line_number, offset, text, _)
            if code:
                self.__full_error_results.append(
                    {'id': code,
                     'line': line_number,
                     'column': offset + 1,
                     'info': text})

        def full_error_results(self):
            """Return error results in detail.

            Results are in the form of a list of dictionaries. Each dictionary
            contains 'id', 'line', 'column', and 'info'.

            """
            return self.__full_error_results

    checker = pep8.Checker('', lines=source,
                           reporter=QuietReport, **pep8_options)
    checker.check_all()
    return checker.report.full_error_results()


class Reindenter(object):

    """Reindents badly-indented code to uniformly use four-space indentation.

    Released to the public domain, by Tim Peters, 03 October 2000.

    """

    def __init__(self, input_text, newline):
        self.newline = newline

        # Raw file lines.
        self.raw = input_text
        self.after = None

        self.string_content_line_numbers = multiline_string_lines(
            ''.join(self.raw))

        # File lines, rstripped & tab-expanded. Dummy at start is so
        # that we can use tokenize's 1-based line numbering easily.
        # Note that a line is all-blank iff it is a newline.
        self.lines = []
        for line_number, line in enumerate(self.raw, start=1):
            # Do not modify if inside a multiline string.
            if line_number in self.string_content_line_numbers:
                self.lines.append(line)
            else:
                # Only expand leading tabs.
                self.lines.append(_get_indentation(line).expandtabs() +
                                  line.strip() + newline)

        self.lines.insert(0, None)
        self.index = 1  # index into self.lines of next line

    def run(self):
        """Fix indentation and return modified line numbers.

        Line numbers are indexed at 1.

        """
        try:
            stats = reindent_stats(tokenize.generate_tokens(self.getline))
        except (tokenize.TokenError, IndentationError):
            return set()
        # Remove trailing empty lines.
        lines = self.lines
        while lines and lines[-1] == self.newline:
            lines.pop()
        # Sentinel.
        stats.append((len(lines), 0))
        # Map count of leading spaces to # we want.
        have2want = {}
        # Program after transformation.
        after = self.after = []
        # Copy over initial empty lines -- there's nothing to do until
        # we see a line with *something* on it.
        i = stats[0][0]
        after.extend(lines[1:i])
        for i in range(len(stats) - 1):
            thisstmt, thislevel = stats[i]
            nextstmt = stats[i + 1][0]
            have = _leading_space_count(lines[thisstmt])
            want = thislevel * 4
            if want < 0:
                # A comment line.
                if have:
                    # An indented comment line. If we saw the same
                    # indentation before, reuse what it most recently
                    # mapped to.
                    want = have2want.get(have, -1)
                    if want < 0:
                        # Then it probably belongs to the next real stmt.
                        for j in range(i + 1, len(stats) - 1):
                            jline, jlevel = stats[j]
                            if jlevel >= 0:
                                if have == _leading_space_count(lines[jline]):
                                    want = jlevel * 4
                                break
                    if want < 0:           # Maybe it's a hanging
                                           # comment like this one,
                        # in which case we should shift it like its base
                        # line got shifted.
                        for j in range(i - 1, -1, -1):
                            jline, jlevel = stats[j]
                            if jlevel >= 0:
                                want = (have + _leading_space_count(
                                        after[jline - 1]) -
                                        _leading_space_count(lines[jline]))
                                break
                    if want < 0:
                        # Still no luck -- leave it alone.
                        want = have
                else:
                    want = 0
            assert want >= 0
            have2want[have] = want
            diff = want - have
            if diff == 0 or have == 0:
                after.extend(lines[thisstmt:nextstmt])
            else:
                for line_number, line in enumerate(lines[thisstmt:nextstmt],
                                                   start=thisstmt):
                    if line_number in self.string_content_line_numbers:
                        after.append(line)
                    elif diff > 0:
                        if line == self.newline:
                            after.append(line)
                        else:
                            after.append(' ' * diff + line)
                    else:
                        remove = min(_leading_space_count(line), -diff)
                        after.append(line[remove:])

        if self.raw == self.after:
            return set()
        else:
            return (set(range(1, 1 + len(self.raw))) -
                    self.string_content_line_numbers)

    def fixed_lines(self):
        return self.after

    def getline(self):
        """Line-getter for tokenize."""
        if self.index >= len(self.lines):
            line = ''
        else:
            line = self.lines[self.index]
            self.index += 1
        return line


def reindent_stats(tokens):
    """Return list  of (lineno, indentlevel) pairs.

    One for each stmt and comment line. indentlevel is -1 for comment lines, as
    a signal that tokenize doesn't know what to do about them; indeed, they're
    our headache!

    """
    find_stmt = 1  # next token begins a fresh stmt?
    level = 0  # current indent level
    stats = []

    for t in tokens:
        token_type = t[0]
        sline = t[2][0]
        line = t[4]

        if token_type == tokenize.NEWLINE:
            # A program statement, or ENDMARKER, will eventually follow,
            # after some (possibly empty) run of tokens of the form
            #     (NL | COMMENT)* (INDENT | DEDENT+)?
            find_stmt = 1

        elif token_type == tokenize.INDENT:
            find_stmt = 1
            level += 1

        elif token_type == tokenize.DEDENT:
            find_stmt = 1
            level -= 1

        elif token_type == tokenize.COMMENT:
            if find_stmt:
                stats.append((sline, -1))
                # but we're still looking for a new stmt, so leave
                # find_stmt alone

        elif token_type == tokenize.NL:
            pass

        elif find_stmt:
            # This is the first "real token" following a NEWLINE, so it
            # must be the first token of the next program statement, or an
            # ENDMARKER.
            find_stmt = 0
            if line:   # not endmarker
                stats.append((sline, level))

    return stats


class Wrapper(object):

    """Class for functions relating to continuation lines and line folding.

    Each instance operates on a single logical line.

    """

    SKIP_TOKENS = frozenset([
        tokenize.COMMENT, tokenize.NL, tokenize.INDENT,
        tokenize.DEDENT, tokenize.NEWLINE, tokenize.ENDMARKER
    ])

    def __init__(self, physical_lines):
        self.lines = physical_lines
        self.tokens = []
        self.rel_indent = None
        sio = StringIO(''.join(physical_lines))
        for t in tokenize.generate_tokens(sio.readline):
            if not len(self.tokens) and t[0] in self.SKIP_TOKENS:
                continue
            if t[0] != tokenize.ENDMARKER:
                self.tokens.append(t)

        self.logical_line = self.build_tokens_logical(self.tokens)

    def build_tokens_logical(self, tokens):
        """Build a logical line from a list of tokens.

        Return the logical line and a list of (offset, token) tuples. Does
        not mute strings like the version in pep8.py.

        """
        # from pep8.py with minor modifications
        logical = []
        previous = None
        for t in tokens:
            token_type, text = t[0:2]
            if token_type in self.SKIP_TOKENS:
                continue
            if previous:
                end_line, end = previous[3]
                start_line, start = t[2]
                if end_line != start_line:  # different row
                    prev_text = self.lines[end_line - 1][end - 1]
                    if prev_text == ',' or (prev_text not in '{[('
                                            and text not in '}])'):
                        logical.append(' ')
                elif end != start:  # different column
                    fill = self.lines[end_line - 1][end:start]
                    logical.append(fill)
            logical.append(text)
            previous = t
        logical_line = ''.join(logical)
        assert logical_line.lstrip() == logical_line
        assert logical_line.rstrip() == logical_line
        return logical_line

    def pep8_expected(self):
        """Replicate logic in pep8.py, to know what level to indent things to.

        Return a list of lists; each list represents valid indent levels for
        the line in question, relative from the initial indent. However, the
        first entry is the indent level which was expected.

        """
        # What follows is an adjusted version of
        # pep8.py:continuation_line_indentation. All of the comments have been
        # stripped and the 'yield' statements replaced with 'pass'.
        if not self.tokens:
            return  # pragma: no cover

        first_row = self.tokens[0][2][0]
        nrows = 1 + self.tokens[-1][2][0] - first_row

        # here are the return values
        valid_indents = [list()] * nrows
        indent_level = self.tokens[0][2][1]
        valid_indents[0].append(indent_level)

        if nrows == 1:
            # bug, really.
            return valid_indents  # pragma: no cover

        indent_next = self.logical_line.endswith(':')

        row = depth = 0
        parens = [0] * nrows
        self.rel_indent = rel_indent = [0] * nrows
        indent = [indent_level]
        indent_chances = {}
        last_indent = (0, 0)
        last_token_multiline = None

        for token_type, text, start, end, _ in self.tokens:
            newline = row < start[0] - first_row
            if newline:
                row = start[0] - first_row
                newline = (not last_token_multiline and
                           token_type not in (tokenize.NL, tokenize.NEWLINE))

            if newline:
                # This is where the differences start. Instead of looking at
                # the line and determining whether the observed indent matches
                # our expectations, we decide which type of indentation is in
                # use at the given indent level, and return the offset. This
                # algorithm is susceptible to "carried errors", but should
                # through repeated runs eventually solve indentation for
                # multiline expressions less than PEP8_PASSES_MAX lines long.

                if depth:
                    for open_row in range(row - 1, -1, -1):
                        if parens[open_row]:
                            break
                else:
                    open_row = 0

                # That's all we get to work with. This code attempts to
                # "reverse" the below logic, and place into the valid indents
                # list
                vi = []
                add_second_chances = False
                if token_type == tokenize.OP and text in ']})':
                    # this line starts with a closing bracket, so it needs to
                    # be closed at the same indent as the opening one.
                    if indent[depth]:
                        # hanging indent
                        vi.append(indent[depth])
                    else:
                        # visual indent
                        vi.append(indent_level + rel_indent[open_row])
                elif depth and indent[depth]:
                    # visual indent was previously confirmed.
                    vi.append(indent[depth])
                    add_second_chances = True
                elif depth and True in indent_chances.values():
                    # visual indent happened before, so stick to
                    # visual indent this time.
                    if depth > 1 and indent[depth - 1]:
                        vi.append(indent[depth - 1])
                    else:
                        # stupid fallback
                        vi.append(indent_level + 4)
                    add_second_chances = True
                elif not depth:
                    vi.append(indent_level + 4)
                else:
                    # must be in hanging indent
                    hang = rel_indent[open_row] + 4
                    vi.append(indent_level + hang)

                # about the best we can do without look-ahead
                if (indent_next and vi[0] == indent_level + 4 and
                        nrows == row + 1):
                    vi[0] += 4

                if add_second_chances:
                    # visual indenters like to line things up.
                    min_indent = vi[0]
                    for col, what in indent_chances.items():
                        if col > min_indent and (
                            what is True or
                            (what == str and token_type == tokenize.STRING) or
                            (what == text and token_type == tokenize.OP)
                        ):
                            vi.append(col)
                    vi = sorted(vi)

                valid_indents[row] = vi

                # Returning to original continuation_line_indentation() from
                # pep8.
                visual_indent = indent_chances.get(start[1])
                last_indent = start
                rel_indent[row] = start[1] - indent_level
                hang = rel_indent[row] - rel_indent[open_row]

                if token_type == tokenize.OP and text in ']})':
                    pass
                elif visual_indent is True:
                    if not indent[depth]:
                        indent[depth] = start[1]

            # line altered: comments shouldn't define a visual indent
            if parens[row] and not indent[depth] and token_type not in (
                tokenize.NL, tokenize.COMMENT
            ):
                indent[depth] = start[1]
                indent_chances[start[1]] = True
            elif token_type == tokenize.STRING or text in (
                'u', 'ur', 'b', 'br'
            ):
                indent_chances[start[1]] = str

            if token_type == tokenize.OP:
                if text in '([{':
                    depth += 1
                    indent.append(0)
                    parens[row] += 1
                elif text in ')]}' and depth > 0:
                    prev_indent = indent.pop() or last_indent[1]
                    for d in range(depth):
                        if indent[d] > prev_indent:
                            indent[d] = 0
                    for ind in list(indent_chances):
                        if ind >= prev_indent:
                            del indent_chances[ind]
                    depth -= 1
                    if depth and indent[depth]:  # modified
                        indent_chances[indent[depth]] = True
                    for idx in range(row, -1, -1):
                        if parens[idx]:
                            parens[idx] -= 1
                            break
                assert len(indent) == depth + 1
                if start[1] not in indent_chances:
                    indent_chances[start[1]] = text

            last_token_multiline = (start[0] != end[0])

        return valid_indents


def _leading_space_count(line):
    """Return number of leading spaces in line."""
    i = 0
    while i < len(line) and line[i] == ' ':
        i += 1
    return i


def refactor_with_2to3(source_text, fixer_names):
    """Use lib2to3 to refactor the source.

    Return the refactored source code.

    """
    from lib2to3.refactor import RefactoringTool
    fixers = ['lib2to3.fixes.fix_' + name for name in fixer_names]
    tool = RefactoringTool(fixer_names=fixers, explicit=fixers)
    return unicode(tool.refactor_string(source_text, name=''))


def break_multiline(source_text, newline, indent_word):
    """Break first line of multiline code.

    Return None if a break is not possible.

    """
    indentation = _get_indentation(source_text)

    # Handle special case only.
    for symbol in '([{':
        # Only valid if symbol is not on a line by itself.
        if (symbol in source_text and not source_text.strip() == symbol):

            if not source_text.rstrip()[-1] == ',':
                continue

            index = 1 + source_text.find(symbol)

            if index <= len(indent_word) + len(indentation):
                continue

            if is_probably_inside_string_or_comment(source_text, index - 1):
                continue

            return (
                source_text[:index].rstrip() + newline +
                indentation + indent_word +
                source_text[index:].lstrip())

    return None


def is_probably_inside_string_or_comment(line, index):
    """Return True if index may be inside a string or comment."""
    # Make sure we are not in a string.
    for quote in ['"', "'"]:
        if quote in line:
            if line.find(quote) <= index:
                return True

    # Make sure we are not in a comment.
    if '#' in line:
        if line.find('#') <= index:
            return True

    return False


def check_syntax(code):
    """Return True if syntax is okay."""
    try:
        return compile(code, '<string>', 'exec')
    except (SyntaxError, TypeError, UnicodeDecodeError):
        return False


def filter_results(source, results, aggressive=False):
    """Filter out spurious reports from pep8.

    If aggressive is True, we allow possibly unsafe fixes (E711, E712).

    """
    non_docstring_string_line_numbers = multiline_string_lines(
        source, include_docstrings=False)
    all_string_line_numbers = multiline_string_lines(
        source, include_docstrings=True)

    split_source = [None] + source.splitlines()

    for r in results:
        issue_id = r['id'].lower()

        if r['line'] in non_docstring_string_line_numbers:
            if issue_id.startswith('e1'):
                continue
            elif issue_id in ['e501', 'w191']:
                continue

        if r['line'] in all_string_line_numbers:
            if issue_id in ['e501']:
                continue

        # Filter out incorrect E101 reports when there are no tabs.
        # pep8 will complain about this even if the tab indentation found
        # elsewhere is in a multiline string.
        if issue_id == 'e101' and '\t' not in split_source[r['line']]:
            continue

        if issue_id in ['e711', 'e712'] and not aggressive:
            continue

        yield r


def multiline_string_lines(source, include_docstrings=False):
    """Return line numbers that are within multiline strings.

    The line numbers are indexed at 1.

    Docstrings are ignored.

    """
    sio = StringIO(source)
    line_numbers = set()
    previous_token_type = ''
    try:
        for t in tokenize.generate_tokens(sio.readline):
            token_type = t[0]
            start_row = t[2][0]
            end_row = t[3][0]
            start_row = t[2][0]
            end_row = t[3][0]

            if (token_type == tokenize.STRING and start_row != end_row):
                if (include_docstrings or
                        previous_token_type != tokenize.INDENT):
                    # We increment by one since we want the contents of the
                    # string.
                    line_numbers |= set(range(1 + start_row, 1 + end_row))

            previous_token_type = token_type
    except (IndentationError, tokenize.TokenError):
        pass

    return line_numbers


def shorten_comment(line, newline, max_line_length):
    """Return trimmed or split long comment line."""
    assert len(line) > max_line_length
    line = line.rstrip()

    # PEP 8 recommends 72 characters for comment text.
    indentation = _get_indentation(line) + '# '
    max_line_length = min(max_line_length,
                          len(indentation) + 72)

    MIN_CHARACTER_REPEAT = 5
    if (len(line) - len(line.rstrip(line[-1])) >= MIN_CHARACTER_REPEAT and
            not line[-1].isalnum()):
        # Trim comments that end with things like ---------
        return line[:max_line_length] + newline
    elif re.match(r'\s*#+\s*\w+', line):
        import textwrap
        split_lines = textwrap.wrap(line.lstrip(' \t#'),
                                    initial_indent=indentation,
                                    subsequent_indent=indentation,
                                    width=max_line_length,
                                    break_long_words=False,
                                    break_on_hyphens=False)
        return newline.join(split_lines) + newline
    else:
        return line + newline


def normalize_line_endings(lines):
    """Return fixed line endings.

    All lines will be modified to use the most common line ending.

    """
    newline = find_newline(lines)
    return [line.rstrip('\n\r') + newline for line in lines]


def mutual_startswith(a, b):
    return b.startswith(a) or a.startswith(b)


def code_match(code, select, ignore):
    if ignore:
        for ignored_code in [c.strip() for c in ignore]:
            if mutual_startswith(code.lower(), ignored_code.lower()):
                return False

    if select:
        for selected_code in [c.strip() for c in select]:
            if mutual_startswith(code.lower(), selected_code.lower()):
                return True
        return False

    return True


def fix_string(source, options=None):
    """Return fixed source code."""
    if not options:
        options = parse_args([''])[0]

    sio = StringIO(source)
    return fix_lines(sio.readlines(), options=options)


def fix_lines(source_lines, options, filename=''):
    """Return fixed source code."""
    tmp_source = unicode().join(normalize_line_endings(source_lines))

    # Keep a history to break out of cycles.
    previous_hashes = set([hash(tmp_source)])

    # Apply global fixes only once (for efficiency).
    fixed_source = apply_global_fixes(tmp_source, options)

    passes = 0
    while True:
        if options.pep8_passes >= 0 and passes > options.pep8_passes:
            break
        passes += 1

        tmp_source = copy.copy(fixed_source)

        fix = FixPEP8(filename, options, contents=tmp_source)
        fixed_source = fix.fix()

        if hash(fixed_source) in previous_hashes:
            break
        else:
            previous_hashes.add(hash(fixed_source))

    return fixed_source


def fix_file(filename, options=None, output=None):
    if not options:
        options = parse_args([filename])[0]

    original_source = read_from_filename(filename, readlines=True)

    fixed_source = original_source

    if options.in_place or output:
        encoding = detect_encoding(filename)

    if output:
        output = codecs.getwriter(encoding)(output.buffer
                                            if hasattr(output, 'buffer')
                                            else output)

        output = LineEndingWrapper(output)

    fixed_source = fix_lines(fixed_source, options, filename=filename)

    if options.diff:
        new = StringIO(fixed_source)
        new = new.readlines()
        diff = get_diff_text(original_source, new, filename)
        if output:
            output.write(diff)
            output.flush()
        else:
            return diff
    elif options.in_place:
        fp = open_with_encoding(filename, encoding=encoding,
                                mode='w')
        fp.write(fixed_source)
        fp.close()
    else:
        if output:
            output.write(fixed_source)
            output.flush()
        else:
            return fixed_source


def global_fixes():
    """Yield multiple (code, function) tuples."""
    for function in globals().values():
        if inspect.isfunction(function):
            arguments = inspect.getargspec(function)[0]
            if arguments != ['source']:
                continue

            code = extract_code_from_function(function)
            if code:
                yield (code, function)


def apply_global_fixes(source, options):
    """Run global fixes on source code.

    Thsese are fixes that only need be done once (unlike those in FixPEP8,
    which are dependent on pep8).

    """
    for (code, function) in global_fixes():
        if code_match(code, select=options.select, ignore=options.ignore):
            if options.verbose:
                print('--->  Applying global fix for {0}'.format(code.upper()),
                      file=sys.stderr)
            source = function(source)

    return source


def extract_code_from_function(function):
    """Return code handled by function."""
    if not function.__name__.startswith('fix_'):
        return None

    code = re.sub('^fix_', '', function.__name__)
    if not code:
        return None

    try:
        int(code[1:])
    except ValueError:
        return None

    return code


def parse_args(args):
    """Parse command-line options."""
    parser = OptionParser(usage='Usage: autopep8 [options] '
                                '[filename [filename ...]]'
                                '\nUse filename \'-\'  for stdin.',
                          version='%prog {0}'.format(__version__),
                          description=__doc__.split('\n')[0],
                          prog='autopep8')
    parser.add_option('-v', '--verbose', action='count', dest='verbose',
                      default=0,
                      help='print verbose messages; '
                           'multiple -v result in more verbose messages')
    parser.add_option('-d', '--diff', action='store_true', dest='diff',
                      help='print the diff for the fixed source')
    parser.add_option('-i', '--in-place', action='store_true',
                      help='make changes to files in place')
    parser.add_option('-r', '--recursive', action='store_true',
                      help='run recursively; must be used with --in-place or '
                           '--diff')
    parser.add_option('-j', '--jobs', type=int, metavar='n', default=1,
                      help='number of parallel jobs; '
                           'match CPU count if value is less than 1')
    parser.add_option('-p', '--pep8-passes', metavar='n',
                      default=-1, type=int,
                      help='maximum number of additional pep8 passes '
                           '(default: infinite)')
    parser.add_option('-a', '--aggressive', action='count', default=0,
                      help='enable non-whitespace changes; '
                           'multiple -a result in more aggressive changes')
    parser.add_option('--exclude', metavar='globs',
                      help='exclude files/directories that match these '
                           'comma-separated globs')
    parser.add_option('--list-fixes', action='store_true',
                      help='list codes for fixes; '
                           'used by --ignore and --select')
    parser.add_option('--ignore', metavar='errors', default='',
                      help='do not fix these errors/warnings '
                           '(default: {0})'.format(DEFAULT_IGNORE))
    parser.add_option('--select', metavar='errors', default='',
                      help='fix only these errors/warnings (e.g. E4,W)')
    parser.add_option('--max-line-length', metavar='n', default=79, type=int,
                      help='set maximum allowed line length '
                           '(default: %default)')
    options, args = parser.parse_args(args)

    if not len(args) and not options.list_fixes:
        parser.error('incorrect number of arguments')

    if '-' in args and len(args) > 1:
        parser.error('cannot mix stdin and regular files')

    if len(args) > 1 and not (options.in_place or options.diff):
        parser.error('autopep8 only takes one filename as argument '
                     'unless the "--in-place" or "--diff" options are '
                     'used')

    if options.recursive and not (options.in_place or options.diff):
        parser.error('--recursive must be used with --in-place or --diff')

    if options.exclude and not options.recursive:
        parser.error('--exclude is only relevant when used with --recursive')

    if options.in_place and options.diff:
        parser.error('--in-place and --diff are mutually exclusive')

    if options.max_line_length <= 0:
        parser.error('--max-line-length must be greater than 0')

    if args == ['-'] and (options.in_place or options.recursive):
        parser.error('--in-place or --recursive cannot be used with '
                     'standard input')

    if options.select:
        options.select = options.select.split(',')

    if options.ignore:
        options.ignore = options.ignore.split(',')
    elif not options.select:
        if options.aggressive:
            # Enable everything by default if aggressive.
            options.select = ['E', 'W']
        else:
            options.ignore = DEFAULT_IGNORE.split(',')

    if options.exclude:
        options.exclude = options.exclude.split(',')
    else:
        options.exclude = []

    if options.jobs < 1:
        # Do not import multiprocessing globally in case it is not supported
        # on the platform.
        import multiprocessing
        options.jobs = multiprocessing.cpu_count()

    if options.jobs > 1 and not options.in_place:
        parser.error('parallel jobs requires --in-place')

    return options, args


def supported_fixes():
    """Yield pep8 error codes that autopep8 fixes.

    Each item we yield is a tuple of the code followed by its description.

    """
    instance = FixPEP8(filename=None, options=None, contents='')
    for attribute in dir(instance):
        code = re.match('fix_([ew][0-9][0-9][0-9])', attribute)
        if code:
            yield (code.group(1).upper(),
                   re.sub(r'\s+', ' ',
                          getattr(instance, attribute).__doc__))

    for (code, function) in sorted(global_fixes()):
        yield (code.upper() + (4 - len(code)) * ' ',
               re.sub(r'\s+', ' ', function.__doc__))


def line_shortening_rank(candidate, newline, indent_word):
    """Return rank of candidate.

    This is for sorting candidates.

    """
    rank = 0
    if candidate.strip():
        lines = candidate.split(newline)

        offset = 0
        if lines[0].rstrip()[-1] not in '([{':
            for symbol in '([{':
                offset = max(offset, 1 + lines[0].find(symbol))

        max_length = max([offset + len(x.strip()) for x in lines])
        rank += max_length
        rank += len(lines)

        bad_staring_symbol = {
            '(': ')',
            '[': ']',
            '{': '}'}.get(lines[0][-1], None)

        if len(lines) > 1:
            if (bad_staring_symbol and
                    lines[1].lstrip().startswith(bad_staring_symbol)):
                rank += 20
            else:
                rank -= 10

        if lines[0].endswith('(['):
            rank += 10

        for current_line in lines:
            for bad_start in ['.', '%', '+', '-', '/']:
                if current_line.startswith(bad_start):
                    rank += 100

            for ending in '([{':
                # Avoid lonely opening. They result in longer lines.
                if (current_line.endswith(ending) and
                        len(current_line.strip()) <= len(indent_word)):
                    rank += 100

            if current_line.endswith('%'):
                rank -= 20

            # Try to break list comprehensions at the "for".
            if current_line.lstrip().startswith('for'):
                rank -= 50
    else:
        rank = 100000

    return max(0, rank)


def split_at_offsets(line, offsets):
    """Split line at offsets.

    Return list of strings.

    """
    result = []

    previous_offset = 0
    current_offset = 0
    for current_offset in sorted(offsets):
        if current_offset < len(line) and previous_offset != current_offset:
            result.append(line[previous_offset:current_offset])
        previous_offset = current_offset

    result.append(line[current_offset:])

    return result


def get_longest_length(text, newline):
    """Return length of longest line."""
    return max([len(line) for line in text.split(newline)])


class LineEndingWrapper(object):

    r"""Replace line endings to work with sys.stdout.

    It seems that sys.stdout expects only '\n' as the line ending, no matter
    the platform. Otherwise, we get repeated line endings.

    """

    def __init__(self, output):
        self.__output = output

    def write(self, s):
        self.__output.write(s.replace('\r\n', '\n').replace('\r', '\n'))

    def flush(self):
        self.__output.flush()


def temporary_file():
    """Return temporary file."""
    try:
        return tempfile.NamedTemporaryFile(mode='w', encoding='utf-8')
    except TypeError:
        return tempfile.NamedTemporaryFile(mode='w')


def match_file(filename, exclude):
    """Return True if file is okay for modifying/recursing."""
    if os.path.basename(filename).startswith('.'):
        return False

    for pattern in exclude:
        if fnmatch.fnmatch(filename, pattern):
            return False

    if not is_python_file(filename):
        return False

    return True


def find_files(filenames, recursive, exclude):
    """Yield filenames."""
    while filenames:
        name = filenames.pop(0)
        if recursive and os.path.isdir(name):
            for root, directories, children in os.walk(name):
                filenames += [os.path.join(root, f) for f in children
                              if match_file(f, exclude)]
                directories[:] = [d for d in directories
                                  if not d.startswith('.')]
        else:
            yield name


def _fix_file(parameters):
    """Helper function for optionally running fix_file() in parallel."""
    if parameters[1].verbose:
        print('[file:{0}]'.format(parameters[0]), file=sys.stderr)
    try:
        fix_file(*parameters)
    except IOError as error:
        print(str(error), file=sys.stderr)


def fix_multiple_files(filenames, options, output=None):
    """Fix list of files.

    Optionally fix files recursively.

    """
    filenames = find_files(filenames, options.recursive, options.exclude)
    if options.jobs > 1:
        import multiprocessing
        pool = multiprocessing.Pool(options.jobs)
        pool.map(_fix_file,
                 [(name, options) for name in filenames])
    else:
        for name in filenames:
            _fix_file((name, options, output))


def is_python_file(filename):
    """Return True if filename is Python file."""
    if filename.endswith('.py'):
        return True

    try:
        with open_with_encoding(filename) as f:
            first_line = f.readlines(1)[0]
    except (IOError, IndexError):
        return False

    if len(first_line) > 200:
        # This is probably not even a text file.
        return False

    if not PYTHON_SHEBANG_REGEX.match(first_line):
        return False

    return True


def main():
    """Tool main."""
    try:
        # Exit on broken pipe.
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except AttributeError:  # pragma: no cover
        # SIGPIPE is not available on Windows.
        pass

    try:
        options, args = parse_args(sys.argv[1:])

        if options.list_fixes:
            for code, description in supported_fixes():
                print('{code} - {description}'.format(
                    code=code, description=description))
            return 0

        if options.in_place or options.diff:
            filenames = list(set(args))
        else:
            assert len(args) == 1
            assert not options.recursive
            if args == ['-']:
                assert not options.in_place
                temp = temporary_file()
                temp.write(sys.stdin.read())
                temp.flush()
                filenames = [temp.name]
            else:
                filenames = args[:1]

        fix_multiple_files(filenames, options, sys.stdout)
    except KeyboardInterrupt:
        return 1  # pragma: no cover


if __name__ == '__main__':
    sys.exit(main())
