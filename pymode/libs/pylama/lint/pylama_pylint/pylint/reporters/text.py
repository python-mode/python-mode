# Copyright (c) 2003-2013 LOGILAB S.A. (Paris, FRANCE).
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
"""Plain text reporters:

:text: the default one grouping messages by module
:colorized: an ANSI colorized text reporter
"""

import warnings

from logilab.common.ureports import TextWriter
from logilab.common.textutils import colorize_ansi

from pylint.interfaces import IReporter
from pylint.reporters import BaseReporter, Message

TITLE_UNDERLINES = ['', '=', '-', '.']


class TextReporter(BaseReporter):
    """reports messages and layouts in plain text"""

    __implements__ = IReporter
    name = 'text'
    extension = 'txt'
    line_format = '{C}:{line:3d},{column:2d}: {msg} ({symbol})'

    def __init__(self, output=None):
        BaseReporter.__init__(self, output)
        self._modules = {}
        self._template = None

    def on_set_current_module(self, module, filepath):
        self._template = unicode(self.linter.config.msg_template or self.line_format)

    def write_message(self, msg):
        """Convenience method to write a formated message with class default template"""
        self.writeln(msg.format(self._template))

    def add_message(self, msg_id, location, msg):
        """manage message of different type and in the context of path"""
        m = Message(self, msg_id, location, msg)
        if m.module not in self._modules:
            if m.module:
                self.writeln('************* Module %s' % m.module)
                self._modules[m.module] = 1
            else:
                self.writeln('************* ')
        self.write_message(m)

    def _display(self, layout):
        """launch layouts display"""
        print >> self.out
        TextWriter().format(layout, self.out)


class ParseableTextReporter(TextReporter):
    """a reporter very similar to TextReporter, but display messages in a form
    recognized by most text editors :

    <filename>:<linenum>:<msg>
    """
    name = 'parseable'
    line_format = '{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}'

    def __init__(self, output=None):
        warnings.warn('%s output format is deprecated. This is equivalent to --msg-template=%s'
                      % (self.name, self.line_format))
        TextReporter.__init__(self, output)


class VSTextReporter(ParseableTextReporter):
    """Visual studio text reporter"""
    name = 'msvs'
    line_format = '{path}({line}): [{msg_id}({symbol}){obj}] {msg}'


class ColorizedTextReporter(TextReporter):
    """Simple TextReporter that colorizes text output"""

    name = 'colorized'
    COLOR_MAPPING = {
        "I" : ("green", None),
        'C' : (None, "bold"),
        'R' : ("magenta", "bold, italic"),
        'W' : ("blue", None),
        'E' : ("red", "bold"),
        'F' : ("red", "bold, underline"),
        'S' : ("yellow", "inverse"), # S stands for module Separator
    }

    def __init__(self, output=None, color_mapping=None):
        TextReporter.__init__(self, output)
        self.color_mapping = color_mapping or \
                             dict(ColorizedTextReporter.COLOR_MAPPING)

    def _get_decoration(self, msg_id):
        """Returns the tuple color, style associated with msg_id as defined
        in self.color_mapping
        """
        try:
            return self.color_mapping[msg_id[0]]
        except KeyError:
            return None, None

    def add_message(self, msg_id, location, msg):
        """manage message of different types, and colorize output
        using ansi escape codes
        """
        msg = Message(self, msg_id, location, msg)
        if msg.module not in self._modules:
            color, style = self._get_decoration('S')
            if msg.module:
                modsep = colorize_ansi('************* Module %s' % msg.module,
                                       color, style)
            else:
                modsep = colorize_ansi('************* %s' % msg.module,
                                       color, style)
            self.writeln(modsep)
            self._modules[msg.module] = 1
        color, style = self._get_decoration(msg.C)
        for attr in ('msg', 'symbol', 'category', 'C'):
            setattr(msg, attr, colorize_ansi(getattr(msg, attr), color, style))
        self.write_message(msg)


def register(linter):
    """Register the reporter classes with the linter."""
    linter.register_reporter(TextReporter)
    linter.register_reporter(ParseableTextReporter)
    linter.register_reporter(VSTextReporter)
    linter.register_reporter(ColorizedTextReporter)
