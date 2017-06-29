"""Astroid hooks for dateutil"""

import textwrap

from astroid import MANAGER, register_module_extender
from astroid.builder import AstroidBuilder

def dateutil_transform():
    return AstroidBuilder(MANAGER).string_build(textwrap.dedent('''
    import datetime
    def parse(timestr, parserinfo=None, **kwargs):
        return datetime.datetime()
    '''))

register_module_extender(MANAGER, 'dateutil.parser', dateutil_transform)
