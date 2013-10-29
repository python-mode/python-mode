from __future__ import absolute_import

import vim
from autopep8 import fix_file


class Options():
    aggressive = 0
    diff = False
    ignore = ''
    in_place = True
    max_line_length = 79
    pep8_passes = 100
    recursive = False
    select = ''
    verbose = 0


def fix_current_file():
    fix_file(vim.current.buffer.name, Options)
