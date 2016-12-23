========
Overview
========



A fast and thorough lazy object proxy.

* Free software: BSD license

Installation
============

::

    pip install lazy-object-proxy

Documentation
=============

https://python-lazy-object-proxy.readthedocs.org/

Development
===========

To run the all tests run::

    tox

Acknowledgements
================

This project is based on some code from `wrapt <https://github.com/GrahamDumpleton/wrapt>`_
as you can see in the git history.


Changelog
=========

1.2.2 (2016-04-14)
------------------

* Added `manylinux <https://www.python.org/dev/peps/pep-0513/>`_ wheels.
* Minor cleanup in readme.

1.2.1 (2015-08-18)
------------------

* Fix a memory leak (the wrapped object would get bogus references). Contributed by Astrum Kuo in
  `#10 <https://github.com/ionelmc/python-lazy-object-proxy/pull/10>`_.

1.2.0 (2015-07-06)
------------------

* Don't instantiate the object when __repr__ is called. This aids with debugging (allows one to see exactly in
  what state the proxy is).

1.1.0 (2015-07-05)
------------------

* Added support for pickling. The pickled value is going to be the wrapped object *without* any Proxy container.
* Fixed a memory management issue in the C extension (reference cycles weren't garbage collected due to improper
  handling in the C extension).

1.0.2 (2015-04-11)
-----------------------------------------

* First release on PyPI.


