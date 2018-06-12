# copyright 2003-2012 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
# contact http://www.logilab.fr/ -- mailto:contact@logilab.fr
#
# This file is part of logilab-common.
#
# logilab-common is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 2.1 of the License, or (at your option) any
# later version.
#
# logilab-common is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with logilab-common.  If not, see <http://www.gnu.org/licenses/>.
"""Unicode email support (extends email from stdlib)"""

__docformat__ = "restructuredtext en"

import email
from encodings import search_function
import sys
from email.utils import parseaddr, parsedate
from email.header import decode_header

from datetime import datetime

from six import text_type, binary_type

try:
    from mx.DateTime import DateTime
except ImportError:
    DateTime = datetime

import logilab.common as lgc


def decode_QP(string):
    parts = []
    for decoded, charset in decode_header(string):
        if not charset :
            charset = 'iso-8859-15'
        # python 3 sometimes returns str and sometimes bytes.
        # the 'official' fix is to use the new 'policy' APIs
        # https://bugs.python.org/issue24797
        # let's just handle this bug ourselves for now
        if isinstance(decoded, binary_type):
            decoded = decoded.decode(charset, 'replace')
        assert isinstance(decoded, text_type)
        parts.append(decoded)

    if sys.version_info < (3, 3):
        # decoding was non-RFC compliant wrt to whitespace handling
        # see http://bugs.python.org/issue1079
        return u' '.join(parts)
    return u''.join(parts)

def message_from_file(fd):
    try:
        return UMessage(email.message_from_file(fd))
    except email.errors.MessageParseError:
        return ''

def message_from_string(string):
    try:
        return UMessage(email.message_from_string(string))
    except email.errors.MessageParseError:
        return ''

class UMessage:
    """Encapsulates an email.Message instance and returns only unicode objects.
    """

    def __init__(self, message):
        self.message = message

    # email.Message interface #################################################

    def get(self, header, default=None):
        value = self.message.get(header, default)
        if value:
            return decode_QP(value)
        return value

    def __getitem__(self, header):
        return self.get(header)

    def get_all(self, header, default=()):
        return [decode_QP(val) for val in self.message.get_all(header, default)
                if val is not None]

    def is_multipart(self):
        return self.message.is_multipart()

    def get_boundary(self):
        return self.message.get_boundary()

    def walk(self):
        for part in self.message.walk():
            yield UMessage(part)

    def get_payload(self, index=None, decode=False):
        message = self.message
        if index is None:
            payload = message.get_payload(index, decode)
            if isinstance(payload, list):
                return [UMessage(msg) for msg in payload]
            if message.get_content_maintype() != 'text':
                return payload
            if isinstance(payload, text_type):
                return payload

            charset = message.get_content_charset() or 'iso-8859-1'
            if search_function(charset) is None:
                charset = 'iso-8859-1'
            return text_type(payload or b'', charset, "replace")
        else:
            payload = UMessage(message.get_payload(index, decode))
        return payload

    def get_content_maintype(self):
        return text_type(self.message.get_content_maintype())

    def get_content_type(self):
        return text_type(self.message.get_content_type())

    def get_filename(self, failobj=None):
        value = self.message.get_filename(failobj)
        if value is failobj:
            return value
        try:
            return text_type(value)
        except UnicodeDecodeError:
            return u'error decoding filename'

    # other convenience methods ###############################################

    def headers(self):
        """return an unicode string containing all the message's headers"""
        values = []
        for header in self.message.keys():
            values.append(u'%s: %s' % (header, self.get(header)))
        return '\n'.join(values)

    def multi_addrs(self, header):
        """return a list of 2-uple (name, address) for the given address (which
        is expected to be an header containing address such as from, to, cc...)
        """
        persons = []
        for person in self.get_all(header, ()):
            name, mail = parseaddr(person)
            persons.append((name, mail))
        return persons

    def date(self, alternative_source=False, return_str=False):
        """return a datetime object for the email's date or None if no date is
        set or if it can't be parsed
        """
        value = self.get('date')
        if value is None and alternative_source:
            unix_from = self.message.get_unixfrom()
            if unix_from is not None:
                try:
                    value = unix_from.split(" ", 2)[2]
                except IndexError:
                    pass
        if value is not None:
            datetuple = parsedate(value)
            if datetuple:
                if lgc.USE_MX_DATETIME:
                    return DateTime(*datetuple[:6])
                return datetime(*datetuple[:6])
            elif not return_str:
                return None
        return value
