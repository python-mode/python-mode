# Copyright (c) 2003-2013 LOGILAB S.A. (Paris, FRANCE).
# http://www.logilab.fr/ -- mailto:contact@logilab.fr
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
"""utilities methods and classes for checkers

Base id of standard checkers (used in msg and report ids):
01: base
02: classes
03: format
04: import
05: misc
06: variables
07: exceptions
08: similar
09: design_analysis
10: newstyle
11: typecheck
12: logging
13: string_format
14: string_constant
15-50: not yet used: reserved for future internal checkers.
51-99: perhaps used: reserved for external checkers

The raw_metrics checker has no number associated since it doesn't emit any
messages nor reports. XXX not true, emit a 07 report !

"""

import sys
import tokenize
import warnings
from os.path import dirname

from astroid.utils import ASTWalker
from logilab.common.configuration import OptionsProviderMixIn

from pylint.reporters import diff_string
from pylint.utils import register_plugins

def table_lines_from_stats(stats, old_stats, columns):
    """get values listed in <columns> from <stats> and <old_stats>,
    and return a formated list of values, designed to be given to a
    ureport.Table object
    """
    lines = []
    for m_type in columns:
        new = stats[m_type]
        format = str
        if isinstance(new, float):
            format = lambda num: '%.3f' % num
        old = old_stats.get(m_type)
        if old is not None:
            diff_str = diff_string(old, new)
            old = format(old)
        else:
            old, diff_str = 'NC', 'NC'
        lines += (m_type.replace('_', ' '), format(new), old, diff_str)
    return lines


class BaseChecker(OptionsProviderMixIn, ASTWalker):
    """base class for checkers"""
    # checker name (you may reuse an existing one)
    name = None
    # options level (0 will be displaying in --help, 1 in --long-help)
    level = 1
    # ordered list of options to control the ckecker behaviour
    options = ()
    # messages issued by this checker
    msgs = {}
    # reports issued by this checker
    reports = ()

    def __init__(self, linter=None):
        """checker instances should have the linter as argument

        linter is an object implementing ILinter
        """
        ASTWalker.__init__(self, self)
        self.name = self.name.lower()
        OptionsProviderMixIn.__init__(self)
        self.linter = linter
        # messages that are active for the current check
        self.active_msgs = set()

    def add_message(self, msg_id, line=None, node=None, args=None):
        """add a message of a given type"""
        self.linter.add_message(msg_id, line, node, args)

    def package_dir(self):
        """return the base directory for the analysed package"""
        return dirname(self.linter.base_file)

    # dummy methods implementing the IChecker interface

    def open(self):
        """called before visiting project (i.e set of modules)"""

    def close(self):
        """called after visiting project (i.e set of modules)"""


class BaseRawChecker(BaseChecker):
    """base class for raw checkers"""

    def process_module(self, node):
        """process a module

        the module's content is accessible via the stream object

        stream must implement the readline method
        """
        warnings.warn("Modules that need access to the tokens should "
                      "use the ITokenChecker interface.",
                      DeprecationWarning)
        stream = node.file_stream
        stream.seek(0) # XXX may be removed with astroid > 0.23
        if sys.version_info <= (3, 0):
            self.process_tokens(tokenize.generate_tokens(stream.readline))
        else:
            self.process_tokens(tokenize.tokenize(stream.readline))

    def process_tokens(self, tokens):
        """should be overridden by subclasses"""
        raise NotImplementedError()


class BaseTokenChecker(BaseChecker):
    """Base class for checkers that want to have access to the token stream."""

    def process_tokens(self, tokens):
        """Should be overridden by subclasses."""
        raise NotImplementedError()


def initialize(linter):
    """initialize linter with checkers in this package """
    register_plugins(linter, __path__[0])

__all__ = ('BaseChecker', 'initialize')
