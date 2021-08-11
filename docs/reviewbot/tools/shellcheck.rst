.. _tool-shellcheck:

==========
ShellCheck
==========

.. versionadded:: 3.0

ShellCheck_ is a static analysis tool for bash/sh/ksh/dash shell scripts that
provides warnings for easy-to-miss issues and suggestions for best practices.

.. _ShellCheck: https://www.shellcheck.net/


Supported File Types
====================

The following are supported by this tool:

* Shell Scripts: :file:`*.bash`, :file:`*.bats`, :file:`*.dash`,
  :file:`*.ksh`, :file:`*.sh`

It will also check any files starting with a shebang (``#!``) line pointing to
:command:`bash`, :command:`dash`, :command:`ksh`, or :command:`sh`.


Installation
============

:command:`shellcheck` can be installed through your package manager.
See ShellCheck's `installation instructions`_ for more information.


.. _installation instructions:
   https://github.com/koalaman/shellcheck#installing


Configuration
=============

ShellCheck Location
-------------------

If the :command:`shellcheck` command is in a non-standard location, and can't
be found in Review Bot's :envvar:`PATH` environment variable, then you'll need
to :ref:`specify the path <worker-configuration-exe-paths>` in the
:ref:`Review Bot worker config file <worker-configuration>`:

.. code-block:: python

    exe_paths = {
        'shellcheck': '/path/to/shellcheck',
    }

You will need to restart the Review Bot worker after making this change.


Enabling ShellCheck in Review Board
-----------------------------------

First, you'll need to add a Review Bot configuration in Review Board (see
:ref:`extension-configuration-tools`).

The following configuration options are available:

:guilabel:`Minimum severity` (required):
    The minimum severity level for commenting on issues. The following
    choices are available, in order of severity:

    * :guilabel:`style` -- Reports on style issues, or anything more severe
    * :guilabel:`info` -- Reports on informative suggestions, or anything
      more severe
    * :guilabel:`warning` -- Reports on warnings in code, or anything more
      severe
    * :guilabel:`error` -- Reports on errors in code

    This is equivalent to :command:`shellcheck --severity=...`.

:guilabel:`Exclude` (optional):
    A comma-separated list of error codes to exclude.

    This is equivalent to :command:`shellcheck --exclude=...`.

    See the list of `shellcheck error codes`_ for possible values.


.. _shellcheck error codes: https://github.com/koalaman/shellcheck/wiki/Checks
