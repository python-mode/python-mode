"""Module level docstring.

Multi line.

Docstring.

"""

import math
import functools


def dec_logger(func):
    """One liner."""
    @functools.wraps(func)
    def wrapper(*arg, **kargs):
        """Imperative one liner."""
        result = func(*arg, **kargs)
        print(result)
        return result
    return wrapper


def n1(x):  # noqa
    """Multi line
    Docstring.
    """
    a = x + 1

    def n2(y):
        """Single line docstring."""
        @dec_logger
        def n3(z):
            """Have multiline.
            Docstring
            As
            Well
            """


            # Leave some blank spaces





            return str(z) + 'expanded'

        b = y + 1
        n3(b)
        return b
    n2(a)


if __name__ == '__main__':
    n1(math.pi)
