"""Astroid hooks for the Python 2 qt4 module.

Currently help understanding of :

* PyQT4.QtCore
"""

from astroid import MANAGER, register_module_extender
from astroid.builder import AstroidBuilder


def pyqt4_qtcore_transform():
    return AstroidBuilder(MANAGER).string_build('''

def SIGNAL(signal_name): pass

class QObject(object):
    def emit(self, signal): pass
''')


register_module_extender(MANAGER, 'PyQt4.QtCore', pyqt4_qtcore_transform)
