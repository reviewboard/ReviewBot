.. _tool-flake8:

======
Flake8
======

flake8_ is a wrapper around several Python code quality tools
(including :ref:`tool-pycodestyle` and :ref:`tool-pyflakes`), which checks for
errors or formatting inconsistencies in Python source code.


.. _flake8: https://flake8.pycqa.org/


Supported File Types
====================

The following are supported by this tool:

* Python: :file:`*.py`


Installation
============

:command:`flake8` can be installed on most systems by running::

    $ pip install flake8

It may also be available in your system's package manager.


Configuration
=============

Flake8 Location
---------------

If the :command:`flake8` command is in a non-standard location, and can't be
found in Review Bot's :envvar:`PATH` environment variable, then you'll need to
:ref:`specify the path <worker-configuration-exe-paths>` in the
:ref:`Review Bot worker config file <worker-configuration>`:

.. code-block:: python

    exe_paths = {
        'flake8': '/path/to/flake8',
    }

You will need to restart the Review Bot worker after making this change.


Enabling Flake8 in Review Board
-------------------------------

First, you'll need to add a Review Bot configuration in Review Board (see
:ref:`extension-configuration-tools`).

The following configuration options are available:

:guilabel:`Maximum line length` (required):
    The maximum length allowed for lines. Any lines longer than this length
    will cause an issue to be filed.

    The default is 79.

    This is equivalent to :command:`flake8 --max-line-length=...`.

:guilabel:`Ignore` (optional):
    A comma-separated list of error or warning codes to ignore.

    This is equivalent to :command:`flake8 --ignore=...`.
