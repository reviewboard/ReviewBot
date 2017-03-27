.. _tool-clang:

=====================
Clang Static Analyzer
=====================

The `Clang Static Analyzer`_ will attempt to compile your C, C++, or Objective
C source code and then check for common programming errors.

.. _Clang Static Analyzer: https://clang-analyzer.llvm.org/


Installation
============

This tool requires a modern version of the Clang_ compiler to be installed on
the system running the Review Bot worker. This is available through most system
package managers on Linux and via the XCode command line tools on Mac OS.

.. _Clang: https://clang.llvm.org/


Configuration
=============

This tool requires full repository access, which is available for Git
repositories. Each repository you intend to use must be configured in the
Review Bot worker config file. See :ref:`worker-configuration` for more
details.

Because C, C++, and Objective C source code often requires numerous external
dependencies or compile-time flags, the tool configuration allows you to
specify additional command line arguments that will be passed to
:command:`clang`. It's recommended that you set up the worker on a system which
is already set up to build your software in order to ensure that the necessary
build environment is available.
