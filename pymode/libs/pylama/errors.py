""" Don't duplicate same errors from different linters. """

from collections import defaultdict


DUPLICATES = (

    # multiple statements on one line
    [('pep8', 'E701'), ('pylint', 'C0321')],

    # unused variable
    [('pylint', 'W0612'), ('pyflakes', 'W0612')],

    # undefined variable
    [('pylint', 'E0602'), ('pyflakes', 'E0602')],

    # unused import
    [('pylint', 'W0611'), ('pyflakes', 'W0611')],

    # whitespace before ')'
    [('pylint', 'C0326'), ('pep8', 'E202')],

    # whitespace before '('
    [('pylint', 'C0326'), ('pep8', 'E211')],

    # multiple spaces after operator
    [('pylint', 'C0326'), ('pep8', 'E222')],

    # missing whitespace around operator
    [('pylint', 'C0326'), ('pep8', 'E225')],

    # unexpected spaces
    [('pylint', 'C0326'), ('pep8', 'E251')],

    # long lines
    [('pylint', 'C0301'), ('pep8', 'E501')],

    # statement ends with a semicolon
    [('pylint', 'W0301'), ('pep8', 'E703')],

    # multiple statements on one line
    [('pylint', 'C0321'), ('pep8', 'E702')],

    # bad indentation
    [('pylint', 'W0311'), ('pep8', 'E111')],

    # wildcart import
    [('pylint', 'W00401'), ('pyflakes', 'W0401')],

    # module docstring
    [('pep257', 'D100'), ('pylint', 'C0111')],

)

DUPLICATES = dict((key, values) for values in DUPLICATES for key in values)


def remove_duplicates(errors):
    """ Filter duplicates from given error's list. """
    passed = defaultdict(list)
    for error in errors:
        key = error.linter, error.number
        if key in DUPLICATES:
            if key in passed[error.lnum]:
                continue
            passed[error.lnum] = DUPLICATES[key]
        yield error


class Error(object):

    """ Store an error's information. """

    def __init__(self, linter="", col=1, lnum=1, type="E",
                 text="unknown error", filename="", **kwargs):
        """ Init error information with default values. """
        text = ' '.join(str(text).strip().split('\n'))
        if linter:
            text = "%s [%s]" % (text, linter)
        number = text.split(' ', 1)[0]
        self._info = dict(linter=linter, col=col, lnum=lnum, type=type[:1],
                          text=text, filename=filename, number=number)

    def __getattr__(self, name):
        return self._info[name]

    def __getitem__(self, name):
        return self._info[name]

    def get(self, name, default=None):
        """ Implement dictionary `get` method. """
        return self._info.get(name, default)

    def __repr__(self):
        return "<Error: %s %s>" % (self.number, self.linter)

# pylama:ignore=W0622,D,R0924
