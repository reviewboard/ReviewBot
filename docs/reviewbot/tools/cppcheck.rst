.. _tool-cppcheck:

========
Cppcheck
========

Cppcheck_ is a tool that does static analysis on C and C++ code.


.. _CPPCheck: http://cppcheck.sourceforge.net/


Supported File Types
====================

The following are supported by this tool:

* C/C++: :file:`*.c`, :file:`*.cc`, :file:`*.cpp`, :file:`*.cxx`,
  :file:`*.c++`, :file:`*.h`, :file:`*.hh`, :file:`*.hpp`, :file:`*.hxx`,
  :file:`*.h++`, :file:`*.tpp`, :file:`*.txx`


Installation
============

The :command:`cppcheck` tool is available in most system package managers.

On Ubuntu/Debian:

.. code-block:: console

    $ sudo apt-get install cppcheck

On RHEL/CentOS/Fedora:

.. code-block:: console

    $ sudo yum install cppcheck

On macOS using Homebrew_:

.. code-block:: console

    $ brew install cppcheck

See the `Cppcheck downloads page`_ for other options.


.. _Cppcheck downloads page: http://cppcheck.sourceforge.net/#download
.. _Homebrew: https://brew.sh/


Configuration
=============

Cppcheck Location
-----------------

If the :command:`cppcheck` command is in a non-standard location, and can't
be found in Review Bot's :envvar:`PATH` environment variable, then you'll
need to :ref:`specify the path <worker-configuration-exe-paths>` in the
:ref:`Review Bot worker config file <worker-configuration>`:

.. code-block:: python

    exe_paths = {
        'cppcheck': '/path/to/cppcheck',
    }

You will need to restart the Review Bot worker after making this change.


Enabling Cppcheck in Review Board
---------------------------------

First, you'll need to add a Review Bot configuration in Review Board (see
:ref:`extension-configuration-tools`).

The following configuration options are available:

:guilabel:`Enable standard style checks`:
    Enable this checkbox if you want to check for style-related issues, which
    will include code style, warning, and performance checks.

    This is equivalent to :command:`cppcheck --enable=style`.

:guilabel:`Enable all error checks`:
    Enable this checkbox if you want to include all possible checks.

    Note that this may include false positives.

    This is equivalent to :command:`cppcheck --enable=all`.

:guilabel:`Force cppcheck to use a specific language` (optional):
    Force Cppcheck into a mode where it assumes all code is either C or
    C++. By default, the language is auto-detected.

    This is equivalent to :command:`cppcheck --language=c` or
    :command:`cppcheck --language=c++`.
