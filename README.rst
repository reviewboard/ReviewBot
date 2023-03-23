==========
Review Bot
==========

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


Supported Code Checking Tools
=============================

Review Bot can perform automated code reviews using any of the following
tools:


C/C++
-----

* `Clang Static Analyzer
  <https://www.reviewboard.org/docs/reviewbot/latest/tools/clang/>`_
  - Compiles and checks C/C++/Objective-C code for a variety of problems

* `Cppcheck
  <https://www.reviewboard.org/docs/reviewbot/latest/tools/cppcheck/>`_
  - Checks C/C++ code for undefined behavior and dangerous coding constructs

* `CppLint <https://www.reviewboard.org/docs/reviewbot/latest/tools/cpplint/>`_
  - Checks C++ code against Google's style guide


Go
--

* `gofmt <https://www.reviewboard.org/docs/reviewbot/latest/tools/gofmt/>`_
  - Checks Go code for code formatting issues

* `Go Tool <https://www.reviewboard.org/docs/reviewbot/latest/tools/gotool/>`_
  - Checks Go code using ``go vet`` and ``go test``


Java
----

* `checkstyle
  <https://www.reviewboard.org/docs/reviewbot/latest/tools/checkstyle/>`_
  - Checks Java code for code formatting issues and code standard
  inconsistencies


JavaScript
----------

* `JSHint <https://www.reviewboard.org/docs/reviewbot/latest/tools/jshint/>`_
  - Checks JavaScript code for common errors


Python
------

* `doc8 <https://www.reviewboard.org/docs/reviewbot/latest/tools/doc8/>`_
  - Check ReStructuredText documentation for styling and syntax errors

* `flake8 <https://www.reviewboard.org/docs/reviewbot/latest/tools/flake8/>`_
  - Checks Python code using a variety of common code Python quality tools

* `pycodestyle
  <https://www.reviewboard.org/docs/reviewbot/latest/tools/pycodestyle/>`_
  - Checks Python code for code formatting issues

* `pydocstyle
  <https://www.reviewboard.org/docs/reviewbot/latest/tools/pydocstyle/>`_
  - Checks Python docstrings for errors and common formatting issues

* `pyflakes
  <https://www.reviewboard.org/docs/reviewbot/latest/tools/pyflakes/>`_
  - Checks Python code for missing imports, unused or undefined variables or
  functions, and more


Ruby
----

* `RuboCop
  <https://www.reviewboard.org/docs/reviewbot/latest/tools/rubocop/>`_
  - Checks Ruby code for common code formatting issues


Rust
----

* `Cargo Tool
  <https://www.reviewboard.org/docs/reviewbot/latest/tools/cargotool/>`_
  - Checks Rust code for errors and suspicious constructs

* `rustfmt
  <https://www.reviewboard.org/docs/reviewbot/latest/tools/rustfmt/>`_
  - Checks Rust code for code formatting issues based on the automatic
  formatting rules in ``rustfmt``


Shell Scripts
-------------

* `ShellCheck
  <https://www.reviewboard.org/docs/reviewbot/latest/tools/shellcheck/>`_
  - Checks Bash/sh scripts for common problems and misused commands


Multi-Language Tools
--------------------

* `FBInfer
  <https://www.reviewboard.org/docs/reviewbot/latest/tools/fbinfer/>`_
  - Checks a wide range of programming languages for potential errors

* `PMD <https://www.reviewboard.org/docs/reviewbot/latest/tools/pmd/>`_
  - Checks code in a variety of programming languages for syntax errors and
  other problems

* `Secret Scanner
  <https://www.reviewboard.org/docs/reviewbot/latest/tools/rbsecretscanner/>`_
  - Checks source code and configuration files for accidental inclusion of
  sensitive keys and credentials

See the links above for installation and usage instructions.


Installing Review Bot
=====================

Review Bot is made up of a message broker, at least one `Review Bot worker`_,
the `Review Bot extension`_ for Review Board, and various code checking tools.

`Official Docker images`_ are also available.

See the `downloads page`_ and read the `Review Bot documentation`_ to learn
how to install and configure Review Bot and its components.


.. _downloads page: https://www.reviewboard.org/downloads/reviewbot/
.. _Official Docker images:
   https://www.reviewboard.org/docs/reviewbot/latest/installation/docker/
.. _Review Bot documentation:
   https://www.reviewboard.org/docs/reviewbot/latest/
.. _Review Bot extension: https://pypi.org/project/reviewbot-extension/
.. _Review Bot worker: https://pypi.org/project/reviewbot-worker/


Getting Support
===============

We can help you get going with Review Bot, and diagnose any issues that may
come up. There are three levels of support: Public Community Support, Private
Basic Support, and Private Premium Support.

The public community support is available on our main `discussion list`_. We
generally respond to requests within a couple of days. This support works well
for general, non-urgent questions that don't need to expose confidential
information.

Private Support plans are available through support contracts. We offer
same-day support options, handled confidentially over e-mail or our support
tracker, and can assist with a wide range of requests.

See your `support options`_ for more information.


.. _discussion list: https://groups.google.com/group/reviewboard/
.. _support options: https://www.reviewboard.org/support/


Reporting Bugs
==============

Hit a bug? Let us know by
`filing a bug report <https://www.reviewboard.org/bugs/new/>`_.

You can also look through the
`existing bug reports <https://www.reviewboard.org/bugs/>`_ to see if anyone
else has already filed the bug.

If you have a `Review Board support contract`_, feel free to reach out to us
for any support issues.


Contributing
============

Are you a developer? Do you want to help build new tools or features for
Review Bot? Great! Let's help you get started.

First off, read through our `Contributor Guide`_.

We accept patches to Review Bot, Review Board, RBTools, and other related
projects on `reviews.reviewboard.org <https://reviews.reviewboard.org/>`_.
(Please note that we *do not* accept pull requests.)

Got any questions about anything related to Review Board and development? Head
on over to our `development discussion list`_.

.. _`Contributor Guide`: https://www.reviewboard.org/docs/codebase/dev/
.. _`development discussion list`:
   https://groups.google.com/group/reviewboard-dev/


Related Projects
================

* `Review Board`_ -
  Our extensible, open source code review tool.
* RBTools_ -
  The RBTools command line suite.
* `RB Gateway`_ -
  Manages Git repositories, providing a full API enabling all of Review Board's
  feaures.

.. _RBTools: https://github.com/reviewboard/rbtools/
.. _ReviewBot: https://github.com/reviewboard/ReviewBot/
.. _RB Gateway: https://github.com/reviewboard/rb-gateway/
