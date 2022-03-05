.. _tool-jshint:

======
JSHint
======

JSHint_ is a tool which checks JavaScript code for common errors, including
style consistency errors.

.. _JSHint: http://jshint.com/


Supported File Types
====================

The following are supported by this tool:

* JavaScript: :file:`*.js`

Additional file extensions can be specified by configuring the
:ref:`Extra file extensions <tool-jshint-config-extra-file-extensions>`
option.


Installation
============

This tool requires a Node.js_ install.

Once installed, you can install JSHint by running::

    $ sudo npm install -g jshint

It may also be available in your system's package manager.


.. _Node.js: https://nodejs.org/


Configuration
=============

JSHint Location
---------------

If the :command:`jshint` command is in a non-standard location, and can't
be found in Review Bot's :envvar:`PATH` environment variable, then you'll
need to :ref:`specify the path <worker-configuration-exe-paths>` in the
:ref:`Review Bot worker config file <worker-configuration>`:

.. code-block:: python

    exe_paths = {
        'jshint': '/path/to/jshint',
    }

You will need to restart the Review Bot worker after making this change.


Enabling JSHint in Review Board
-------------------------------

First, you'll need to add a Review Bot configuration in Review Board (see
:ref:`extension-configuration-tools`).

The following configuration options are available:


.. _tool-jshint-config-extra-file-extensions:

:guilabel:`Extra file extensions` (optional):
    A comma-separated list of additional file extensions to run JSHint on.

    This should look like: ``.ext1, .ext2, .ext3``

:guilabel:`Extract JavaScript from HTML` (optional):
    Whether JavaScript content in HTML files should be extracted and checked.
    The following choices are available:

    * :guilabel:`Auto` - Extracts only if it thinks the file is an HTML file
    * :guilabel:`Always` - Always treats a file as possible HTML
    * :guilabel:`Never` - Never extracts JavaScript from a non-JavaScript
      file

    If specifying this, you will want to add ``.html`` or suitable template
    extensions in :ref:`Extra file extensions
    <tool-jshint-config-extra-file-extensions>`.

    This is equivalent to :command:`jshint --extract=...`.

:guilabel:`Configuration` (optional):
    A custom JSON configuration for JSHint.

    Callers should be sure to validate this configuration before setting it.

    This is equivalent to :command:`jshint --config=...` with a path to a
    file containing the provided configuration.
