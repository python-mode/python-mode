import vim
from pylibs.autopep8 import fix_file


class Options():
    verbose = 0
    diff = False
    in_place = True
    recursive = False
    pep8_passes = 100
    ignore = ''
    select = ''


def fix_current_file():
    fix_file(vim.current.buffer.name, Options)
