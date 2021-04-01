.. _tool-pmd:

===
PMD
===

PMD_ is a static analysis tool that provides a variety of checkers for many
languages.

.. _PMD: https://pmd.github.io/


Installation
============

PMD can be installed through many system package managers, or downloaded and
installed manually.


Configuration
=============

PMD Location
------------

Because there are a variety of methods to install PMD, there's no consistent
location (or name) of the PMD executable. If installed through a package
manager, it can often be invoked via :command:`pmd`. If installed manually,
it's invoked via :command:`run.sh`.

If it's not named :command:`pmd`, or can't be found in Review Bot's
:envvar:`PATH` environment variable, then you'll need to specify the path
in the :ref:`Review Bot worker config file <worker-configuration>`:

.. code-block:: python

    exe_paths = {
        'pmd': '/path/to/pmd',
    }

You will need to restart the Review Bot worker after making this change.


.. note:: This setting was renamed in Review Bot 3.0.

   In Review Bot 2.0, this setting was called ``pmd_path``. For consistency,
   the old setting was deprecated in 3.0, and will be removed in 4.0.

   See :ref:`upgrading-config-3.0`.


Enabling PMD in Review Board
----------------------------

First, you'll need to add a Review Bot configuration in Review Board (see
:ref:`extension-configuration-tools`).

The following fields are available:

:guilabel:`Rulesets` (required):
    This can be one of the following:

    1. A comma-separated list of `PMD rulesets`_ to apply (equivalent to
       :command:`pmd -rulesets ...`).

    2. A full `PMD ruleset configuration file`_ (starting with
       ``<?xml ...?>``).

:guilabel:`Scan files` (optional):
    A comma-separated list of file extensions to scan. Only files in the diff
    that match these file extensions will trigger the PMD configuration.

    If not provided, the tool will be ran for all files in the diff.

    For example: ``c,js,py``


.. _PMD rulesets: https://pmd.github.io/latest/pmd_rules_java.html
.. _PMD ruleset configuration file:
   https://pmd.github.io/latest/pmd_userdocs_making_rulesets.html
