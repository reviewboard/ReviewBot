.. _tool-rubocop:

=======
RuboCop
=======

.. versionadded:: 3.0

The RuboCop_ tool will check Ruby source code for any coding errors, or any
formatting not in compliance with the `community Ruby style guide`_.


.. _RuboCop: https://docs.rubocop.org
.. _community Ruby style guide: https://rubystyle.guide/


Supported File Types
====================

The following are supported by this tool.

* Ruby: :file:`*.rb`


Installation
============

This tool requires that both Ruby_ and the :command:`rubocop` command line
tool are installed on the system running the Review Bot worker.

If Ruby is installed, :command:`rubocop` can be installed by running::

    $ gem install rubocop

It may also be available in your system's package manager.


.. _Ruby: https://www.ruby-lang.org/


Configuration
=============

RuboCop Location
----------------

If the :command:`rubocop` command is in a non-standard location, and can't
be found in Review Bot's :envvar:`PATH` environment variable, then you'll
need to :ref:`specify the path <worker-configuration-exe-paths>` in the
:ref:`Review Bot worker config file <worker-configuration>`:

.. code-block:: python

    exe_paths = {
        'rubocop': '/path/to/rubocop',
    }

You will need to restart the Review Bot worker after making this change.


Enabling RuboCop in Review Board
--------------------------------

First, you'll need to add a Review Bot configuration in Review Board (see
:ref:`extension-configuration-tools`).

The following configuration options are available:

:guilabel:`Except` (optional):
    A comma-separated list of cops_ or departments_ that will be excluded
    from any checks.

    This is equivalent to :command:`rubocop --except=...`.


.. _cops: https://docs.rubocop.org/rubocop/cops.html
.. _departments: https://docs.rubocop.org/rubocop/cops.html#available-cops
