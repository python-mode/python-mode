""" Dont duplicate errors same type. """

DUPLICATES = (

    # multiple statements on one line
    [('pep8', 'E701'), ('pylint', 'C0321')],

    # missing whitespace around operator
    [('pep8', 'E225'), ('pylint', 'C0326')],

    # unused variable
    [('pylint', 'W0612'), ('pyflakes', 'W0612')],

    # undefined variable
    [('pylint', 'E0602'), ('pyflakes', 'E0602')],

    # unused import
    [('pylint', 'W0611'), ('pyflakes', 'W0611')],

    # unexpected spaces
    [('pylint', 'C0326'), ('pep8', 'E251')],

    # long lines
    [('pylint', 'C0301'), ('pep8', 'E501')],

    # whitespace before '('
    [('pylint', 'C0326'), ('pep8', 'E211')],

    # statement ends with a semicolon
    [('pylint', 'W0301'), ('pep8', 'E703')],

    # multiple statements on one line
    [('pylint', 'C0321'), ('pep8', 'E702')],

    # bad indentation
    [('pylint', 'W0311'), ('pep8', 'E111')],

)

DUPLICATES = dict((key, values) for values in DUPLICATES for key in values)


class Error(object):

    """ Store error information. """

    def __init__(self, linter="", col=1, lnum=1, type="E",
                 text="unknown error", filename="", **kwargs):
        """ Init error information with default values. """
        text = ' '.join(str(text).strip().split('\n'))
        if linter:
            text = "%s [%s]" % (text, linter)
        number = text.split(' ', 1)[0]
        self._info = dict(linter=linter, col=col, lnum=lnum, type=type,
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
