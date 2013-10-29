""" Custom module loader. """


class Linter(object): # noqa

    """ Abstract class for linter plugin. """

    @staticmethod
    def allow(path):
        """ Check path is relevant for linter.

        :return bool:

        """

        return path.endswith('.py')

    @staticmethod
    def run(path, **meta):
        """ Method 'run' should be defined. """

        raise NotImplementedError(__doc__)


LINTERS = dict()


from os import listdir, path as op

curdir = op.dirname(__file__)
for p in listdir(curdir):
    if p.startswith('pylama') and op.isdir(op.join(curdir, p)):
        name = p[len('pylama_'):]
        module = __import__(
            'pylama.lint.pylama_%s' % name, globals(), locals(), ['Linter'])
        LINTERS[name] = getattr(module, 'Linter')()

# try:
    # from pkg_resources import iter_entry_points

    # for entry in iter_entry_points('pylama.linter'):
        # LINTERS[entry.name] = entry.load()()
# except ImportError:
    # pass
