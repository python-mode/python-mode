# Copyright (c) 2016 Claudiu Popa <pcmanticore@gmail.com>

# Licensed under the LGPL: https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html
# For details: https://github.com/PyCQA/astroid/blob/master/COPYING.LESSER
import sys

import six

import astroid

PY36 = sys.version_info >= (3, 6)

def _hashlib_transform():
    template = '''
    class %(name)s(object):
      def __init__(self, value=''): pass
      def digest(self):
        return %(digest)s
      def copy(self):
        return self
      def update(self, value): pass
      def hexdigest(self):
        return ''
      @property
      def name(self):
        return %(name)r
      @property
      def block_size(self):
        return 1
      @property
      def digest_size(self):
        return 1
    '''
    algorithms = ['md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512']
    if PY36:
        algorithms += [
            'sha3_224', 'sha3_256', 'sha3_384', 'sha3_512', 'shake_128', 'shake_256',
            'blake2b',
        ]
    classes = "".join(
        template % {'name': hashfunc, 'digest': 'b""' if six.PY3 else '""'}
        for hashfunc in algorithms)
    return astroid.parse(classes)


astroid.register_module_extender(astroid.MANAGER, 'hashlib', _hashlib_transform)
