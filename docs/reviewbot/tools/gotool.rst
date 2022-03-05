.. _tool-gotool:

=======
Go Tool
=======

.. versionadded:: 3.0

The Go_ tool allows you to use the code quality and testing tools built in to
the Go toolchain. If configured, this will call out to :command:`go vet` to
inspect your code and :command:`go test` to run unit tests.


.. _Go: https://golang.org/


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


Enabling Full Repository Access
-------------------------------

This tool requires full repository access, which is available for Git and
Mercurial repositories. Each repository you intend to use must be configured
in the Review Bot worker config file.

See :ref:`worker-configuration-repositories` for instructions.


Enabling Go Tool in Review Board
--------------------------------

First, you'll need to add a Review Bot configuration in Review Board (see
:ref:`extension-configuration-tools`).

The following configuration options are available:

:guilabel:`Run tests`:
    Enable this checkbox to run your test suite using :command:`go test`.

:guilabel:`Vet code`:
    Enable this checkbox to perform checks on uploaded Go code using
    :command:`go vet`.
