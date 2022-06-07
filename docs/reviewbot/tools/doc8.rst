.. _tool-doc8:

====
Doc8
====

.. versionadded:: 2.0

Doc8_ is an opinionated style checker for reStructuredText_-based
documentation (including Sphinx_-compatible documentation).

See the `doc8 documentation`_ for the lists of checks that are performed.


.. _Doc8: https://pypi.org/project/doc8
.. _doc8 documentation: https://github.com/pycqa/doc8
.. _reStructuredText: https://docutils.sourceforge.io/rst.html
.. _Sphinx: https://www.sphinx-doc.org/en/master/


Supported File Types
====================

The following are supported by this tool:

* reStructuredText: :file:`*.rst`


Installation
============

:command:`doc8` can be installed on most systems by running:

.. code-block:: console

    $ pip install doc8

It may also be available in your system's package manager.


Configuration
=============

Doc8 Location
-------------

If the :command:`doc8` command is in a non-standard location, and can't
be found in Review Bot's :envvar:`PATH` environment variable, then you'll
need to :ref:`specify the path <worker-configuration-exe-paths>` in the
:ref:`Review Bot worker config file <worker-configuration>`:

.. code-block:: python

    exe_paths = {
        'doc8': '/path/to/doc8',
    }

You will need to restart the Review Bot worker after making this change.


Enabling Doc8 in Review Board
-----------------------------

First, you'll need to add a Review Bot configuration in Review Board (see
:ref:`extension-configuration-tools`).

The following configuration options are available:

:guilabel:`Maximum line length` (required):
    The maximum length allowed for lines. Any lines longer than this length
    will cause an issue to be filed.

    The default is 79.

    This is equivalent to :command:`doc8 --max-line-length=...`.

:guilabel:`Encoding` (required):
    The encoding used for reStructuredText files.

    reStructuredText files using any other encoding may cause parsing
    problems.

    The default is ``utf-8``.

    This is equivalent to :command:`doc8 --file-encoding=...`.
