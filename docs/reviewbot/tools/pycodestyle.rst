.. _tool-pycodestyle:

===========
Pycodestyle
===========

.. versionadded:: 2.0

pycodestyle_ is a tool that checks Python code against a handful of style
conventions, including those defined in :pep:`8`.


.. _pycodestyle: https://pycodestyle.pycqa.org/


Supported File Types
====================

The following are supported by this tool:

* Python: :file:`*.py`


Installation
============

:command:`pycodestyle` can be installed on most systems by running::

    $ pip install pycodestyle

It may also be available in your system's package manager.


Configuration
=============

Pycodestyle Location
--------------------

If the :command:`pycodestyle` command is in a non-standard location, and can't
be found in Review Bot's :envvar:`PATH` environment variable, then you'll need
to :ref:`specify the path <worker-configuration-exe-paths>` in the
:ref:`Review Bot worker config file <worker-configuration>`:

.. code-block:: python

    exe_paths = {
        'pycodestyle': '/path/to/pycodestyle',
    }

You will need to restart the Review Bot worker after making this change.


Enabling pycodestyle in Review Board
------------------------------------

First, you'll need to add a Review Bot configuration in Review Board (see
:ref:`extension-configuration-tools`).

The following configuration options are available:

:guilabel:`Maximum line length` (required):
    The maximum length allowed for lines. Any lines longer than this length
    will cause an issue to be filed.

    The default is 79.

    This is equivalent to :command:`pycodestyle --max-line-length=...`.

:guilabel:`Ignore` (optional):
    A comma-separated list of error or warning codes to ignore.

    This is equivalent to :command:`pycodestyle --ignore=...`.

    See the list of `pycodestyle error codes`_ for possible values.


.. _pycodestyle error codes:
   https://pycodestyle.pycqa.org/en/latest/intro.html#error-codes
