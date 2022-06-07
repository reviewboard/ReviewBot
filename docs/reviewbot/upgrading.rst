.. _upgrading:

====================
Upgrading Review Bot
====================

.. _upgrading-packages:

Upgrading Review Bot Packages
=============================

From Review Bot 1.0 or Newer
----------------------------

Upgrading Review Bot is easy. You'll just need to upgrade the extension,
workers, and then make any necessary configuration changes.


Upgrade the Extension
~~~~~~~~~~~~~~~~~~~~~

To start, upgrade the extension on the Review Board server:

.. code-block:: console

    $ sudo pip install -U reviewbot-extension


Depending on your configuration, you may need to restart or reload your web
server. The specific command depends on your individual setup, but is usually
something like the following:

.. code-block:: console

    $ sudo service httpd reload

Open the Review Board administration page and click :guilabel:`Extensions`.
You should see the new version of Review Bot installed.


Upgrade the Workers
~~~~~~~~~~~~~~~~~~~

You can now upgrade each worker.

If you have a :ref:`manual installation <installation-manual>`, run:

.. code-block:: console

    $ sudo pip install -U reviewbot-worker

(If you're installing in a virtual environment, don't use ``sudo``.)

Then follow the :ref:`upgrading-config` for any configuration changes you may
need to make.

If you're using our :ref:`official Docker images <installation-docker>`, you
can just switch to a newer tag and restart your containers.


From Review Bot 0.1 or 0.2
--------------------------

The configuration of Review Bot 0.1 and 0.2 worked differently than modern
versions, so to start, make a note of all your settings.

Then you'll need to uninstall the old extension on the Review Board server:

.. code-block:: console

    $ sudo pip uninstall Review_Bot_Extension

And then uninstall each worker:

.. code-block:: console

    $ sudo pip uninstall ReviewBot

Then follow the :ref:`installation instructions <installation>` to install a
modern version.


.. _upgrading-config:

Upgrading Review Bot Configuration
==================================


.. _upgrading-config-3.0:

Review Bot 3.0 Configuration Changes
------------------------------------

Deprecated Settings
~~~~~~~~~~~~~~~~~~~

The following configuration settings have been deprecated:

* ``checkstyle_path``

  The :file:`.jar` file should now be specified as an item in a list in
  ``java_classpaths``, keyed off by ``checkstyle``. For example:

  .. code-block:: python

      java_classpaths = {
          'checkstyle': [
              '/opt/checkstyle/checkstyle-X.Y.jar',
          ],
      }

* ``pmd_path``

  This should now be specified as ``pmd`` in ``exe_paths``. For example:

  .. code-block:: python

      exe_paths = {
          'pmd': '/opt/pmd/bin/pmd',
      }

* ``review_board_servers``

  This has been renamed to ``reviewboard_servers``.

Deprecated settings will continue to work until Review Bot 4.0.


Cookie Settings
~~~~~~~~~~~~~~~

In prior releases, Review Board session cookies were stored in the current
directory where Review Bot was run from. They're now stored in a dedicated
cache directory for the user Review Bot is running as.

This path can be configured through the ``cookie_dir`` setting.

See :ref:`worker-configuration-cookies` for details.
