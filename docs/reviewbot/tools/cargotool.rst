.. _tool-cargotool:

==========
Cargo Tool
==========

.. versionadded:: 3.0

The Cargo Tool utilizes functionality from the Cargo toolchain to test and
check Rust code for errors and suspicious constructs. Bugs and abnormal code
constructs detected by this tool can be intercepted before they have shipped to
users, preventing crashes and poor performance in production.

Lint checks are performed using `cargo clippy`_, and unit tests are performed
using `cargo test`_.


.. _cargo clippy: https://github.com/rust-lang/rust-clippy#clippy
.. _cargo test: https://doc.rust-lang.org/cargo/commands/cargo-test.html


Supported File Types
====================

The following are supported by this tool.

* Rust: :file:`*.rs`


Installation
============

Installing Rust and Cargo
-------------------------

This tool requires that Rust/Cargo is installed on the system running the
Review Bot worker. Rust/Cargo is available for download on Linux/Mac/Windows.

See the `Rust installation guide`_ for instructions.


.. _Rust installation guide: https://www.rust-lang.org/tools/install


Installing Clippy
-----------------

In order to use the linting feature, the Cargo component :program:`clippy`
must be installed and configured. Review Bot currently requires this to be
installed even if you don't intend to use this feature.

To install Clippy, run:

.. code-block:: console

    rustup component add clippy

See the `Clippy documentation`_ for more information.


.. _Clippy documentation: https://github.com/rust-lang/rust-clippy#readme


Configuration
=============

Cargo Location
--------------

If the :command:`cargo` command is in a non-standard location, and can't
be found in Review Bot's :envvar:`PATH` environment variable, then you'll
need to :ref:`specify the path <worker-configuration-exe-paths>` in the
:ref:`Review Bot worker config file <worker-configuration>`:

.. code-block:: python

    exe_paths = {
        'cargo': '/path/to/cargo',
        'cargo-clippy': '/path/to/cargo-clippy',
    }

You will need to restart the Review Bot worker after making this change.


Enabling Full Repository Access
-------------------------------

This tool requires full repository access, which is available for Git and
Mercurial repositories. Each repository you intend to use must be configured
in the Review Bot worker config file.

See :ref:`worker-configuration-repositories` for instructions.


Enabling Cargo Tool in Review Board
-----------------------------------

First, you'll need to add a Review Bot configuration in Review Board (see
:ref:`extension-configuration-tools`).

The following configuration options are available:

:guilabel:`Check and lint code`:
    Enable this checkbox if you want to perform lint checks on uploaded Rust
    code.

    This will run :command:`cargo clippy` on the code.

:guilabel:`Run tests`:
    Enable this checkbox if you want to run unit tests on uploaded Rust code.

    Note that this can take some time, depending on the size of the codebase.

    This will run :command:`cargo test` on the code.
