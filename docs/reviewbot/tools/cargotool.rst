.. _tool-cargotool:

==========
Cargo Tool
==========

The Cargo Tool utilizes functionality from the Cargo toolchain to test and
check Rust code for errors and suspicious constructs. Bugs and abnormal code
constructs detected by this tool can be intercepted before they have shipped to
users, preventing crashes and poor performance in production.


Installation
============

This tool requires that Rust/Cargo is installed on the system running the
Review Bot worker. Rust/Cargo is available for download on Linux/Mac/Windows.
See the official documentation on `installing Rust`_.

.. _installing Rust: https://www.rust-lang.org/tools/install


Configuration
=============

In order to use the linting feature, the Cargo component :program:`clippy` must
be installed and configured. This can be done following this command:

.. code-block:: console

    rustup component add clippy

See the official documentation on the `rust-clippy repository`_.

This tool requires full repository access, which is available for Git and
Mercurial repositories. Each repository you intend to use must be configured in
the Review Bot worker config file. See :ref:`worker-configuration` for more
details.

.. _rust-clippy repository: https://github.com/rust-lang/rust-clippy
