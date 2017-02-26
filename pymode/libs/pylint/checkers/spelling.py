# -*- coding: utf-8 -*-
# Copyright (c) 2014-2016 Claudiu Popa <pcmanticore@gmail.com>
# Copyright (c) 2014 LOGILAB S.A. (Paris, FRANCE) <contact@logilab.fr>
# Copyright (c) 2014 Michal Nowikowski <godfryd@gmail.com>
# Copyright (c) 2015 Pavel Roskin <proski@gnu.org>
# Copyright (c) 2015 Ionel Cristian Maries <contact@ionelmc.ro>

# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

"""Checker for spelling errors in comments and docstrings.
"""

import os
import re
import tokenize
import string
import sys

try:
    import enchant
except ImportError:
    enchant = None
import six

from pylint.interfaces import ITokenChecker, IAstroidChecker
from pylint.checkers import BaseTokenChecker
from pylint.checkers.utils import check_messages

if sys.version_info[0] >= 3:
    maketrans = str.maketrans
else:
    maketrans = string.maketrans

if enchant is not None:
    br = enchant.Broker()
    dicts = br.list_dicts()
    dict_choices = [''] + [d[0] for d in dicts]
    dicts = ["%s (%s)" % (d[0], d[1].name) for d in dicts]
    dicts = ", ".join(dicts)
    instr = ""
else:
    dicts = "none"
    dict_choices = ['']
    instr = " To make it working install python-enchant package."

table = maketrans("", "")


class SpellingChecker(BaseTokenChecker):
    """Check spelling in comments and docstrings"""
    __implements__ = (ITokenChecker, IAstroidChecker)
    name = 'spelling'
    msgs = {
        'C0401': ('Wrong spelling of a word \'%s\' in a comment:\n%s\n'
                  '%s\nDid you mean: \'%s\'?',
                  'wrong-spelling-in-comment',
                  'Used when a word in comment is not spelled correctly.'),
        'C0402': ('Wrong spelling of a word \'%s\' in a docstring:\n%s\n'
                  '%s\nDid you mean: \'%s\'?',
                  'wrong-spelling-in-docstring',
                  'Used when a word in docstring is not spelled correctly.'),
        'C0403': ('Invalid characters %r in a docstring',
                  'invalid-characters-in-docstring',
                  'Used when a word in docstring cannot be checked by enchant.'),
        }
    options = (('spelling-dict',
                {'default' : '', 'type' : 'choice', 'metavar' : '<dict name>',
                 'choices': dict_choices,
                 'help' : 'Spelling dictionary name. '
                          'Available dictionaries: %s.%s' % (dicts, instr)}),
               ('spelling-ignore-words',
                {'default' : '',
                 'type' : 'string',
                 'metavar' : '<comma separated words>',
                 'help' : 'List of comma separated words that '
                          'should not be checked.'}),
               ('spelling-private-dict-file',
                {'default' : '',
                 'type' : 'string',
                 'metavar' : '<path to file>',
                 'help' : 'A path to a file that contains private '
                          'dictionary; one word per line.'}),
               ('spelling-store-unknown-words',
                {'default' : 'n', 'type' : 'yn', 'metavar' : '<y_or_n>',
                 'help' : 'Tells whether to store unknown words to '
                          'indicated private dictionary in '
                          '--spelling-private-dict-file option instead of '
                          'raising a message.'}),
              )

    def open(self):
        self.initialized = False
        self.private_dict_file = None

        if enchant is None:
            return
        dict_name = self.config.spelling_dict
        if not dict_name:
            return

        self.ignore_list = [w.strip() for w in self.config.spelling_ignore_words.split(",")]
        # "param" appears in docstring in param description and
        # "pylint" appears in comments in pylint pragmas.
        self.ignore_list.extend(["param", "pylint"])

        # Expand tilde to allow e.g. spelling-private-dict-file = ~/.pylintdict
        if self.config.spelling_private_dict_file:
            self.config.spelling_private_dict_file = os.path.expanduser(
                self.config.spelling_private_dict_file)

        if self.config.spelling_private_dict_file:
            self.spelling_dict = enchant.DictWithPWL(
                dict_name, self.config.spelling_private_dict_file)
            self.private_dict_file = open(
                self.config.spelling_private_dict_file, "a")
        else:
            self.spelling_dict = enchant.Dict(dict_name)

        if self.config.spelling_store_unknown_words:
            self.unknown_words = set()

        # Prepare regex for stripping punctuation signs from text.
        # ' and _ are treated in a special way.
        puncts = string.punctuation.replace("'", "").replace("_", "")
        self.punctuation_regex = re.compile('[%s]' % re.escape(puncts))
        self.initialized = True

    def close(self):
        if self.private_dict_file:
            self.private_dict_file.close()

    def _check_spelling(self, msgid, line, line_num):
        line2 = line.strip()
        # Replace ['afadf with afadf (but preserve don't)
        line2 = re.sub("'([^a-zA-Z]|$)", " ", line2)
        # Replace afadf'] with afadf (but preserve don't)
        line2 = re.sub("([^a-zA-Z]|^)'", " ", line2)
        # Replace punctuation signs with space e.g. and/or -> and or
        line2 = self.punctuation_regex.sub(' ', line2)

        words = []
        for word in line2.split():
            # Skip words with digits.
            if len(re.findall(r"\d", word)) > 0:
                continue

            # Skip words with mixed big and small letters,
            # they are probaly class names.
            if (len(re.findall("[A-Z]", word)) > 0 and
                    len(re.findall("[a-z]", word)) > 0 and
                    len(word) > 2):
                continue

            # Skip words with _ - they are probably function parameter names.
            if word.count('_') > 0:
                continue

            words.append(word)

        # Go through words and check them.
        for word in words:
            # Skip words from ignore list.
            if word in self.ignore_list:
                continue

            orig_word = word
            word = word.lower()

            # Strip starting u' from unicode literals and r' from raw strings.
            if (word.startswith("u'") or
                    word.startswith('u"') or
                    word.startswith("r'") or
                    word.startswith('r"')) and len(word) > 2:
                word = word[2:]

            # If it is a known word, then continue.
            try:
                if self.spelling_dict.check(word):
                    continue
            except enchant.errors.Error:
                # this can only happen in docstrings, not comments
                self.add_message('invalid-characters-in-docstring',
                                 line=line_num, args=(word,))
                continue

            # Store word to private dict or raise a message.
            if self.config.spelling_store_unknown_words:
                if word not in self.unknown_words:
                    self.private_dict_file.write("%s\n" % word)
                    self.unknown_words.add(word)
            else:
                # Present up to 4 suggestions.
                # TODO: add support for customising this.
                suggestions = self.spelling_dict.suggest(word)[:4]

                m = re.search(r"(\W|^)(%s)(\W|$)" % word, line.lower())
                if m:
                    # Start position of second group in regex.
                    col = m.regs[2][0]
                else:
                    col = line.lower().index(word)
                indicator = (" " * col) + ("^" * len(word))

                self.add_message(msgid, line=line_num,
                                 args=(orig_word, line,
                                       indicator,
                                       "' or '".join(suggestions)))

    def process_tokens(self, tokens):
        if not self.initialized:
            return

        # Process tokens and look for comments.
        for (tok_type, token, (start_row, _), _, _) in tokens:
            if tok_type == tokenize.COMMENT:
                self._check_spelling('wrong-spelling-in-comment',
                                     token, start_row)

    @check_messages('wrong-spelling-in-docstring')
    def visit_module(self, node):
        if not self.initialized:
            return
        self._check_docstring(node)

    @check_messages('wrong-spelling-in-docstring')
    def visit_classdef(self, node):
        if not self.initialized:
            return
        self._check_docstring(node)

    @check_messages('wrong-spelling-in-docstring')
    def visit_functiondef(self, node):
        if not self.initialized:
            return
        self._check_docstring(node)

    visit_asyncfunctiondef = visit_functiondef

    def _check_docstring(self, node):
        """check the node has any spelling errors"""
        docstring = node.doc
        if not docstring:
            return

        start_line = node.lineno + 1
        if six.PY2:
            encoding = node.root().file_encoding
            docstring = docstring.decode(encoding or sys.getdefaultencoding(),
                                         'replace')

        # Go through lines of docstring
        for idx, line in enumerate(docstring.splitlines()):
            self._check_spelling('wrong-spelling-in-docstring',
                                 line, start_line + idx)


def register(linter):
    """required method to auto register this checker """
    linter.register_checker(SpellingChecker(linter))
