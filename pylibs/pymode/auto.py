import vim
from pylibs.autopep8 import fix_file, PEP8_PASSES_MAX


class Options():
    verbose = False
    diff = False
    in_place = True
    recursive = False
    pep8_passes = PEP8_PASSES_MAX
    ignore = ''
    select = ''


def fix_current_file():
    fix_file(vim.current.buffer.name, Options)
