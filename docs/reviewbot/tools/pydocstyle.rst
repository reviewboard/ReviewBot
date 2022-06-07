.. _tool-pydocstyle:

===========
Pydocstyle
===========

pydocstyle_ is a static analysis tool to check your checks docstrings in
your Python code against common `docstring conventions`_.


.. _docstring conventions:
   http://www.pydocstyle.org/en/stable/error_codes.html#default-conventions
.. _pydocstyle: http://www.pydocstyle.org/


Supported File Types
====================

The following are supported by this tool:

* Python: :file:`*.py`


Installation
============

:command:`pydocstyle` can be installed on most systems by running:

.. code-block:: console

    $ pip install pydocstyle

It may also be available in your system's package manager.


Configuration
=============

Pydocstyle Location
-------------------

If the :command:`pydocstyle` command is in a non-standard location, and can't
be found in Review Bot's :envvar:`PATH` environment variable, then you'll need
to :ref:`specify the path <worker-configuration-exe-paths>` in the
:ref:`Review Bot worker config file <worker-configuration>`:

.. code-block:: python

    exe_paths = {
        'pydocstyle': '/path/to/pydocstyle',
    }

You will need to restart the Review Bot worker after making this change.


Enabling pydocstyle in Review Board
-----------------------------------

First, you'll need to add a Review Bot configuration in Review Board (see
:ref:`extension-configuration-tools`).

The following configuration options are available:

:guilabel:`Ignore` (optional):
    A comma-separated list of error or warning codes to ignore.

    This is equivalent to :command:`flake8 --ignore=...`.

    See the list of `pydocstyle error codes`_ for possible values.


.. _pydocstyle error codes:
   http://www.pydocstyle.org/en/stable/error_codes.html
