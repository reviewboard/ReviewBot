.. _tool-cpplint:

=======
Cpplint
=======

Cpplint_ is a tool which checks C++ code against `Google's style guide`_.


.. _Cpplint: https://github.com/google/styleguide/tree/gh-pages/cpplint
.. _Google's style guide: https://google.github.io/styleguide/cppguide.html


Supported File Types
====================

The following are supported by this tool:

* C/C++: :file:`*.c`, :file:`*.cc`, :file:`*.cpp`, :file:`*.cu`,
  :file:`*.cuh`, :file:`*.cxx`, :file:`*.c++`, :file:`*.h`, :file:`*.hh`,
  :file:`*.hpp`, :file:`*.hxx`, :file:`*.h++`


Installation
============

:command:`cpplint` can be installed on most systems by running:

.. code-block:: console

    $ pip install cpplint

It may also be available in your system's package manager.


Configuration
=============

Cpplint Location
----------------

If the :command:`cpplint` command is in a non-standard location, and can't
be found in Review Bot's :envvar:`PATH` environment variable, then you'll
need to :ref:`specify the path <worker-configuration-exe-paths>` in the
:ref:`Review Bot worker config file <worker-configuration>`:

.. code-block:: python

    exe_paths = {
        'cpplint': '/path/to/cpplint',
    }

You will need to restart the Review Bot worker after making this change.


Enabling Cpplint in Review Board
--------------------------------

First, you'll need to add a Review Bot configuration in Review Board (see
:ref:`extension-configuration-tools`).

The following configuration options are available:

:guilabel:`Verbosity level for Cpplint` (required):
    The level of verbosity for error reporting. This is a number between 1
    and 5, where 1 will report all warnings/errors, and 5 will report only
    the most severe.

    This is equivalent to :command:`cpplint --verbose=...`.

:guilabel:`Tests to exclude` (optional):
    A comma-separated list of tests to exclude.

    You can see available options by running :command:`cpplint --filter=`
    locally. This is equivalent to passing the filter names to that
    option.
