.. _tool-doc8:

====
doc8
====

.. versionadded:: 2.0

DOC8_ is a style checker for Sphinx (or other) reStructuredText
documentation. Also it has basic support for plain text.
:command:`doc8` uses RST_LINT_ as a backend for the verification.

.. _DOC8: https://pypi.python.org/pypi/doc8
.. _RST_LINT: https://pypi.python.org/pypi/restructuredtext_lint


Checks
======

doc8 verifies the following styles in ``.rst`` files.

* Invalid rst format - D000
* Lines should not be longer than 79 characters - D001

  * RST exception: line with no whitespace except in the beginning
  * RST exception: lines with http or https urls
  * RST exception: literal blocks
  * RST exception: rst target directives

* No trailing whitespace - D002
* No tabulation for indentation - D003
* No carriage returns (use unix newlines) - D004
* No newline at end of file - D005


Installation
============

:command:`doc8` can be installed on most systems by running::

    $ pip install doc8

It may also be available in your system's package manager.
