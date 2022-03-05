.. _tool-gofmt:

======
Go Fmt
======

.. versionadded:: 3.0

The Go_ toolchain includes an automatic formatter, `go fmt`_ which all code is
expected to be run through in order to maintain consistency throughout a
codebase.

This tool will report if :file:`.go` files are incorrectly formatted,
suggesting to the user that they should reformat it.


.. _Go: https://golang.org/
.. _go fmt: https://pkg.go.dev/fmt


Supported File Types
====================

The following are supported by this tool:

* Go: :file:`*.go`


Installation
============

This tool requires that Go_ is installed on the system running the Review
Bot worker. Go is available for download on Linux/Mac/Windows.

See the official documentation on `installing Go`_.


.. _installing Go: https://golang.org/doc/install


Configuration
=============

Go Location
-----------

If the :command:`go` command is in a non-standard location, and can't be found
in Review Bot's :envvar:`PATH` environment variable, then you'll need to
:ref:`specify the path <worker-configuration-exe-paths>` in the
:ref:`Review Bot worker config file <worker-configuration>`:

.. code-block:: python

    exe_paths = {
        'go': '/path/to/go',
    }

You will need to restart the Review Bot worker after making this change.


Enabling Go Fmt in Review Board
-------------------------------

You'll need to add a Review Bot configuration in Review Board (see
:ref:`extension-configuration-tools`).

There are no configuration options available for this tool.
