"""Custom module loader."""


class Linter(object):

    """Abstract class for linter plugin."""

    @staticmethod
    def allow(path):
        """Check path is relevant for linter.

        :return bool:
        """
        return path.endswith('.py')

    @staticmethod
    def run(path, **meta):
        """Method 'run' should be defined."""
        raise NotImplementedError(__doc__)
