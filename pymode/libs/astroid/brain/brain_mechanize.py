from astroid import MANAGER, register_module_extender
from astroid.builder import AstroidBuilder

def mechanize_transform():
    return AstroidBuilder(MANAGER).string_build('''

class Browser(object):
    def open(self, url, data=None, timeout=None):
        return None
    def open_novisit(self, url, data=None, timeout=None):
        return None
    def open_local_file(self, filename):
        return None

''')


register_module_extender(MANAGER, 'mechanize', mechanize_transform)
