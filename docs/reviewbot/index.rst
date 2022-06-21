========================
Review Bot Documentation
========================

.. Make sure this stays roughly in sync with the README.rst in the root of
   the repository.


Welcome to Review Bot!

Review Bot automates parts of the code review process, using a wide range of
industry-standard code checking tools to look over your code and catch
problems so your developers can focus on the bigger picture.

It is:

* **Made for Review Board:** Tools are configured through Review Board's
  existing Integrations_ functionality, letting you choose exactly when and how
  tools are run within your organization.

* **Scalable:** Review Bot is built using Celery_ and can scale out to service
  very large Review Board deployments.

* **Extensible:** Writing plugins is simple using a convenient API to retrieve
  code files and craft a review. If more power is needed, tools can access the
  full Review Board API.

Premium support for Review Bot is included with any `Review Board support
contract`_.


.. _Celery: https://docs.celeryq.dev/
.. _Integrations: https://www.reviewboard.org/docs/manual/latest/admin/integrations/
.. _Review Board: https://www.reviewboard.org/
.. _Review Board support contract: https://www.reviewboard.org/support/


.. _installation:

Getting Started
===============

Review Bot |version| supports Review Board 3.0 or 4.0, and Python 2.7 or
3.6 through 3.10.

A Review Bot setup consists of three pieces:

1. The Review Bot extension for Review Board.
2. A message broker (such as RabbitMQ_).
3. At least one Review Bot worker (either on the Review Board server or
   somewhere else in your network), which will run the code checking tools.

There are two official ways to install Review Bot:

* :doc:`Manual installation <installation/manual>`
* :doc:`Official Docker images <installation/docker>`

Once Review Bot is installed, you'll need to configure the extension and
the workers:

* :ref:`Configuring the extension <extension-configuration>`
* :ref:`Configuring workers <worker-configuration>`
* :ref:`Configuring code checking tools <extension-configuration-tools>`

Ready to upgrade to a new version of Review Bot?

* :doc:`Upgrading Review Bot <upgrading>`

This will guide you through any installation and configuration changes you
need to make.


.. _RabbitMQ: http://www.rabbitmq.com/


.. _tools:

Available Tools
===============

The following tools are supported by Review Bot:


C/C++
-----

* :ref:`Clang Static Analyzer <tool-clang>`
  - Compiles and checks C/C++/Objective-C code for a variety of problems

* :ref:`Cppcheck <tool-cppcheck>`
  - Checks C/C++ code for undefined behavior and dangerous coding constructs

* :ref:`CppLint <tool-cpplint>`
  - Checks C++ code against Google's style guide


Go
--

* :ref:`gofmt <tool-gofmt>`
  - Checks Go code for code formatting issues

* :ref:`Go Tool <tool-gotool>`
  - Checks Go code using ``go vet`` and ``go test``


Java
----

* :ref:`checkstyle <tool-checkstyle>`
  - Checks Java code for code formatting issues and code standard
  inconsistencies


JavaScript
----------

* :ref:`JSHint <tool-jshint>`
  - Checks JavaScript code for common errors


Python
------

* :ref:`doc8 <tool-doc8>`
  - Check ReStructuredText documentation for styling and syntax errors

* :ref:`flake8 <tool-flake8>`
  - Checks Python code using a variety of common code Python quality tools

* :ref:`pycodestyle <tool-pycodestyle>`
  - Checks Python code for code formatting issues

* :ref:`pydocstyle <tool-pydocstyle>`
  - Checks Python docstrings for errors and common formatting issues

* :ref:`pyflakes <tool-pyflakes>`
  - Checks Python code for missing imports, unused or undefined variables or
  functions, and more


Ruby
----

* :ref:`RuboCop <tool-rubocop>`
  - Checks Ruby code for common code formatting issues


Rust
----

* :ref:`Cargo Tool <tool-cargotool>`
  - Checks Rust code for errors and suspicious constructs

* :ref:`rustfmt <tool-rustfmt>`
  - Checks Rust code for code formatting issues based on the automatic
  formatting rules in ``rustfmt``


Shell Scripts
-------------

* :ref:`ShellCheck <tool-shellcheck>`
  - Checks Bash/sh scripts for common problems and misused commands


Multi-Language Tools
--------------------

* :ref:`FBInfer <tool-fbinfer>`
  - Checks a wide range of programming languages for potential errors

* :ref:`PMD <tool-pmd>`
  - Checks code in a variety of programming languages for syntax errors and
  other problems

* :ref:`Review Bot Secret Scanner <tool-rbsecretscanner>`
  - Checks source code and configuration files for accidental inclusion of
  sensitive keys and credentials


Extending Review Bot
====================

Review Bot can be extended through custom tools. To do this, you'll need to
create a :py:class:`reviewbot.tools.base.tool.BaseTool` subclass, registered
through the ``reviewbot.tools`` Python entrypoint in a Python package.

Unit tests can be built using the :py:mod:`reviewbot.tools.testing` module.

See the :ref:`module and class reference <reviewbot-coderef>` for details.




.. toctree::
   :hidden:

   installation/index
   upgrading
   configuration
   tools/index
   coderef/index
