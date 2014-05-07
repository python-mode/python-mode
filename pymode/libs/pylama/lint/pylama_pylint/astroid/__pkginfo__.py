# copyright 2003-2013 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
# contact http://www.logilab.fr/ -- mailto:contact@logilab.fr
#
# This file is part of astroid.
#
# astroid is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation, either version 2.1 of the License, or (at your
# option) any later version.
#
# astroid is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
# for more details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with astroid. If not, see <http://www.gnu.org/licenses/>.
"""astroid packaging information"""

distname = 'astroid'

modname = 'astroid'

numversion = (1, 1, 1)
version = '.'.join([str(num) for num in numversion])

install_requires = ['logilab-common >= 0.60.0']

license = 'LGPL'

author = 'Logilab'
author_email = 'python-projects@lists.logilab.org'
mailinglist = "mailto://%s" % author_email
web = 'http://bitbucket.org/logilab/astroid'

description = "rebuild a new abstract syntax tree from Python's ast"

from os.path import join
include_dirs = ['brain',
                join('test', 'regrtest_data'),
                join('test', 'data'), join('test', 'data2')]

classifiers = ["Topic :: Software Development :: Libraries :: Python Modules",
               "Topic :: Software Development :: Quality Assurance",
               "Programming Language :: Python",
               "Programming Language :: Python :: 2",
               "Programming Language :: Python :: 3",
               ]
