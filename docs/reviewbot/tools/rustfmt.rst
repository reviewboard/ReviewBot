.. _tool-rustfmt:

=======
rustfmt
=======

The Rust toolchain includes an automatic formatter (rustfmt_) which all code is
expected to be run through in order to maintain consistency throughout a
codebase. This tool will provide alerts if :file:`.rs` files are incorrectly
formatted.

.. _rustfmt: https://github.com/rust-lang/rustfmt


Installation
============

This tool requires that Rust and :program:`rustfmt` are installed on the system
running the Review Bot worker. To learn more, see the documentation on
`installing Rust`_ and `installing rustfmt`_.

.. _installing Rust: https://www.rust-lang.org/tools/install
.. _installing rustfmt: https://github.com/rust-lang/rustfmt#quick-start
