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

Because there are a variety of methods to install PMD, there's no consistent
location (or name) of the PMD executable. If installed through a package
manager, it can often be invoked via :command:`pmd`. If installed manually,
it's invoked via :command:`run.sh`.

The path and name of the executable has to be configured in the
:ref:`Review Bot worker config file <worker-configuration>`.

.. code-block:: python

    pmd_path = '/usr/local/bin/pmd'
