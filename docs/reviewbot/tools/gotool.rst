.. _tool-gotool:

=======
Go Tool
=======

The Go tool allows you to use the code quality and testing tools built in to
the Go toolchain. This allows running `go vet` and `go test` on your review
requests.


Installation
============

This tool requires that Go is installed on the system running the Review
Bot worker. Go is available for download on Linux/Mac/Windows. More
information about `installation`_ can be found on the official Go website.

.. _installation: https://golang.org/doc/install


Configuration
=============

This tool requires full repository access, which is available for Git and
Mercurial repositories. Each repository you intend to use must be configured
in the Review Bot worker config file. See :ref:`worker-configuration` for more
details.
