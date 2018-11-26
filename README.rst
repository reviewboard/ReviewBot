==========
Review Bot
==========

Review Bot is a tool for automating tasks on code uploaded to `Review Board`_,
and posting the results as a code review. Review Bot was built to automate the
execution of static analysis tools.

Review Bot is:

* **Extensible:** Writing plugins is simple using a convenient API to retrieve
  code files and craft a review. If more power is needed, tools can access the
  full Review Board API.

* **Scalable:** Review Bot is built using Celery_ and can scale out to service
  very large Review Board instances.

* **Integrated Configuration:** Tools are configured through the Review Board
  admin panel, including settings uniquely defined for each task.


.. _Celery: https://www.celeryproject.org/
.. _Review Board: https://www.reviewboard.org/


Supported Code Checking Tools
=============================

Review Bot can perform automated code reviews using any of the following
tools:

* `BuildBot "try"
  <https://www.reviewboard.org/docs/reviewbot/latest/tools/buildbot/>`_
  - Builds the patch in a configured BuildBot environment

* `checkstyle
  <https://www.reviewboard.org/docs/reviewbot/latest/tools/checkstyle/>`_
  - A static analysis tool that provides a variety of checkers for Java code

* `Cppcheck
  <https://www.reviewboard.org/docs/reviewbot/latest/tools/cppcheck/>`_
  - A static analysis tool for C/C++ code

* `CppLint <https://www.reviewboard.org/docs/reviewbot/latest/tools/cpplint/>`_
  - Checks C++ code against Google's style guide

* `flake8 <https://www.reviewboard.org/docs/reviewbot/latest/tools/flake8/>`_
  - A wrapper around several Python code quality tools

* `PMD <https://www.reviewboard.org/docs/reviewbot/latest/tools/pmd/>`_
  - A static analysis tool that provides checkers for many languages

* `pycodestyle
  <https://www.reviewboard.org/docs/reviewbot/latest/tools/pycodestyle/>`_
  - A code style checker for Python code

* `pydocstyle
  <https://www.reviewboard.org/docs/reviewbot/latest/tools/pydocstyle/>`_
  - A static analysis tool for Python docstring conventions

* `pyflakes <https://www.reviewboard.org/docs/reviewbot/latest/tools/pyflakes/>`_
  - A static analysis tool for Python code

See the links above for installation and usage instructions.


Installing Review Bot
=====================

Review Bot is made up of a message broker, at least one `Review Bot worker`_,
the `Review Bot extension`_ for Review Board, and various code checking tools.

See the `downloads page`_ and read the `Review Bot documentation`_ to learn
how to install and configure Review Bot and its components.

.. _downloads page: https://www.reviewboard.org/downloads/reviewbot/
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


Our Happy Users
===============

There are thousands of companies and organizations using Review Board today.
We respect the privacy of our users, but some of them have asked to feature them
on the `Happy Users page`_.

If you're using Review Board, and you're a happy user,
`let us know! <https://groups.google.com/group/reviewboard/>`_


.. _Happy Users page: https://www.reviewboard.org/users/


Reporting Bugs
==============

Hit a bug? Let us know by
`filing a bug report <https://www.reviewboard.org/bugs/new/>`_.

You can also look through the
`existing bug reports <https://www.reviewboard.org/bugs/>`_ to see if anyone
else has already filed the bug.


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
