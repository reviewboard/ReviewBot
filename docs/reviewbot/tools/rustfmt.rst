.. _tool-rustfmt:

========
Rust Fmt
========

.. versionadded:: 3.0

The Rust toolchain includes an automatic formatter (rustfmt_) which all code is
expected to be run through in order to maintain consistency throughout a
codebase.

This tool will report any syntax errors in Rust source code, or report if
the files are incorrectly formatted, suggesting to the user that they should
reformat it.


.. _rustfmt: https://github.com/rust-lang/rustfmt


Supported File Types
====================

The following are supported by this tool.

* Rust: :file:`*.rs`


Installation
============

This tool requires that Rust and :program:`rustfmt` are installed on the
system running the Review Bot worker.

To learn more, see the documentation on `installing Rust`_ and `installing
rustfmt`_.

.. _installing Rust: https://www.rust-lang.org/tools/install
.. _installing rustfmt: https://github.com/rust-lang/rustfmt#quick-start


Configuration
=============

Rust Fmt Location
-----------------

If the :command:`rustfmt` command is in a non-standard location, and can't be
found in Review Bot's :envvar:`PATH` environment variable, then you'll need to
:ref:`specify the path <worker-configuration-exe-paths>` in the
:ref:`Review Bot worker config file <worker-configuration>`:

.. code-block:: python

    exe_paths = {
        'rustfmt': '/path/to/rustfmt',
    }

You will need to restart the Review Bot worker after making this change.


Enabling Rust Fmt in Review Board
---------------------------------

You'll need to add a Review Bot configuration in Review Board (see
:ref:`extension-configuration-tools`).

There are no configuration options available for this tool.
