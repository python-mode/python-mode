# encoding: iso-8859-15
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
import sys
import email
from os.path import join, dirname, abspath

from six import text_type

from logilab.common.testlib import TestCase, unittest_main
from logilab.common.umessage import UMessage, decode_QP, message_from_string

DATA = join(dirname(abspath(__file__)), 'data')

class UMessageTC(TestCase):

    def setUp(self):
        if sys.version_info >= (3, 2):
            import io
            msg1 = email.message_from_file(io.open(join(DATA, 'test1.msg'), encoding='utf8'))
            msg2 = email.message_from_file(io.open(join(DATA, 'test2.msg'), encoding='utf8'))
        else:
            msg1 = email.message_from_file(open(join(DATA, 'test1.msg')))
            msg2 = email.message_from_file(open(join(DATA, 'test2.msg')))
        self.umessage1 = UMessage(msg1)
        self.umessage2 = UMessage(msg2)

    def test_get_subject(self):
        subj = self.umessage2.get('Subject')
        self.assertEqual(type(subj), text_type)
        self.assertEqual(subj, u'À LA MER')

    def test_get_all(self):
        to = self.umessage2.get_all('To')
        self.assertEqual(type(to[0]), text_type)
        self.assertEqual(to, [u'élément à accents <alf@logilab.fr>'])

    def test_get_payload_no_multi(self):
        payload = self.umessage1.get_payload()
        self.assertEqual(type(payload), text_type)
    
    def test_get_payload_decode(self):
        msg = """\
MIME-Version: 1.0
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: base64
Subject: =?utf-8?q?b=C3=AFjour?=
From: =?utf-8?q?oim?= <oim@logilab.fr>
Reply-to: =?utf-8?q?oim?= <oim@logilab.fr>, =?utf-8?q?BimBam?= <bim@boum.fr>
X-CW: data
To: test@logilab.fr
Date: now

dW4gcGV0aXQgY8O2dWNvdQ==
"""
        msg = message_from_string(msg)
        self.assertEqual(msg.get_payload(decode=True), u'un petit cöucou')

    def test_decode_QP(self):
        test_line =  '=??b?UmFwaGHrbA==?= DUPONT<raphael.dupont@societe.fr>'
        test = decode_QP(test_line)
        self.assertEqual(type(test), text_type)
        self.assertEqual(test, u'Raphaël DUPONT<raphael.dupont@societe.fr>')

    def test_decode_QP_utf8(self):
        test_line = '=?utf-8?q?o=C3=AEm?= <oim@logilab.fr>'
        test = decode_QP(test_line)
        self.assertEqual(type(test), text_type)
        self.assertEqual(test, u'oîm <oim@logilab.fr>')

    def test_decode_QP_ascii(self):
        test_line = 'test <test@logilab.fr>'
        test = decode_QP(test_line)
        self.assertEqual(type(test), text_type)
        self.assertEqual(test, u'test <test@logilab.fr>')


if __name__ == '__main__':
    unittest_main()
