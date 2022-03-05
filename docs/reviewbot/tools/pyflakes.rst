.. _tool-pyflakes:

========
Pyflakes
========

pyflakes_ is a static analysis tool that checks Python code for a variety
of errors or problems in Python source code.

.. _pyflakes: https://pypi.python.org/pypi/pyflakes


Supported File Types
====================

The following are supported by this tool:

* Python: :file:`*.py`


Installation
============

:command:`pyflakes` can be installed on most systems by running::

    $ pip install pyflakes

It may also be available in your system's package manager.


Configuration
=============

Pyflakes Location
-----------------

If the :command:`pyflakes` command is in a non-standard location, and can't be
found in Review Bot's :envvar:`PATH` environment variable, then you'll need to
:ref:`specify the path <worker-configuration-exe-paths>` in the
:ref:`Review Bot worker config file <worker-configuration>`:

.. code-block:: python

    exe_paths = {
        'pyflakes': '/path/to/pyflakes',
    }

You will need to restart the Review Bot worker after making this change.


Enabling pyflakes in Review Board
---------------------------------

You'll need to add a Review Bot configuration in Review Board (see
:ref:`extension-configuration-tools`).

There are no configuration options available for this tool.
