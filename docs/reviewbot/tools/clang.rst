.. _tool-clang:

=====================
Clang Static Analyzer
=====================

The `Clang Static Analyzer`_ will attempt to compile your C, C++, or Objective
C source code and then check for common programming errors.

.. _Clang Static Analyzer: https://clang-analyzer.llvm.org/


Supported File Types
====================

The following are supported by this tool:

* C/C++: :file:`*.c`, :file:`*.cc`, :file:`*.cpp`, :file:`*.cxx`,
  :file:`*.c++`
* Objective-C/C++: :file:`*.m`, :file:`*.mm`


Installation
============

This tool requires a modern version of the Clang_ compiler to be installed on
the system running the Review Bot worker.

On Ubuntu/Debian::

    sudo apt-get install clang clang-tools

On macOS, install the XCode command line tools.

On other Linux distributions or operating systems, you may need to follow the
documentation for your system or check your package manager.

Alternatively, you can attempt to `download Clang`_ and install it manually.


.. _Clang: https://clang.llvm.org/
.. _download Clang: https://releases.llvm.org/download.html


Configuration
=============

Clang Location
--------------

If the :command:`clang` command is in a non-standard location, and can't
be found in Review Bot's :envvar:`PATH` environment variable, then you'll
need to :ref:`specify the path <worker-configuration-exe-paths>` in the
:ref:`Review Bot worker config file <worker-configuration>`:

.. code-block:: python

    exe_paths = {
        'clang': '/path/to/clang',
    }

You will need to restart the Review Bot worker after making this change.


Enabling Full Repository Access
-------------------------------

This tool requires full repository access, which is available for Git and
Mercurial repositories. Each repository you intend to use must be configured
in the Review Bot worker config file.

See :ref:`worker-configuration-repositories` for instructions.


Preparing Your Build Environment
--------------------------------

Because C, C++, and Objective C source code often requires numerous external
dependencies or compile-time flags, the tool configuration allows you to
specify additional command line arguments that will be passed to
:command:`clang`.

It's recommended that you set up the worker on a system which is already set
up to build your software in order to ensure that the necessary build
environment is available.


Enabling Clang in Review Board
------------------------------

First, you'll need to add a Review Bot configuration in Review Board (see
:ref:`extension-configuration-tools`).

The following configuration options are available:

:guilabel:`Clang command-line arguments` (optional):
    Additional command line arguments to pass to :command:`clang -S --analyze`.

    You may want to use this if you need to set specific include paths or
    options needed to build your software.

    Note that ``-ObjC`` or ``-ObjC++`` will be passed automatically if working
    with Objective-C/C++ code.
