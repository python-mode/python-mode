"""
    Code audit tool for python. Pylama wraps these tools:

    * PEP8_ (c) 2012-2013, Florent Xicluna;
    * PyFlakes_ (c) 2005-2013, Kevin Watters;
    * Pylint_ (c) 2013, Logilab;
    * Mccabe_ (c) Ned Batchelder;

    |  `Pylint doesnt supported in python3.`

    :copyright: 2013 by Kirill Klenov.
    :license: BSD, see LICENSE for more details.
"""

version_info = 1, 0, 2

__version__ = version = '.'.join(map(str, version_info))
__project__ = __name__
__author__ = "Kirill Klenov <horneds@gmail.com>"
__license__ = "GNU LGPL"
