.. _configuration:

======================
Configuring Review Bot
======================


.. _extension-configuration:

Extension Configuration
=======================

After the Review Bot extension is enabled, it needs to be configured. Open the
Review Board administration page and click :guilabel:`Extensions` in the top
bar. Under the extension called "Review Bot", click :guilabel:`Configure` to
set up the extension.

There are two items that need to be set here: the user, and the broker URL.

.. image:: extension-configuration@2x.png
   :width: 792
   :height: 556


Review Bot User
---------------

Review Bot uses a special user account to post reviews. If you were previously
using Review Bot 0.1 or 0.2, select the existing Review Bot user. Otherwise,
click :guilabel:`create a new user for Review Bot`.


.. _extension-configuration-broker-url:

Broker URL
----------

For the broker URL, put in the URL of your RabbitMQ or other Celery broker. For
example, if your broker is running on the same system as your Review Board
server, this might look something like::

    amqp://guest:guest@localhost:5672//


Checking Status and Updating Tools List
---------------------------------------

After saving the configuration, the page will attempt to contact the broker and
check for workers. The :guilabel:`Broker Status` box will indicate whether
everything is set up correctly. This will also save a list of the available
tools, which is required for setting up tool configurations.


.. _extension-configuration-tools:

Tool Configurations
===================

To set up a tool to run, open the Review Board administration page and click
:guilabel:`Integrations` in the top bar. Under the Review Bot section, click
:guilabel:`Add a new configuration`.

.. image:: integrations-list@2x.png
   :width: 795
   :height: 355

Each tool configuration allows you to specify a tool to run, the conditions for
when that tool is run, and some options for how it is run.

First, give the configuration a name. You can then choose a set of conditions
for when the tool should run. If you would like it to run on every change,
choose :guilabel:`Always match`. Otherwise, you can select a set of conditions
(such as a specific repository, or an assigned review group).

Next, choose which tool to run. Once a tool is selected, additional
tool-specific options may appear. See the documentation for the :ref:`tool
<tools>` you want to configure for more information.

.. image:: tool-configuration@2x.png
   :width: 807
   :height: 905


.. note:: It's important to be aware that tools will only run if they're
          currently available on a running worker node. If your worker dies,
          items will be added to the queue but will not run. In this case, the
          jobs will appear on the review request but will show as timed out.

.. note:: Some tools may require extra configuration on the worker. Details on
          this can be found below.


.. _worker-configuration:

Worker Configuration
====================

In most cases, the Review Bot worker runs without any configuration other than
the broker URL which is part of the command line.

There are a few special situations which do require additional configuration in
a special Python file which defines variables for the worker.

The location of this file depends on the operating system that the worker is
running on. On Linux, the file should be located at
:file:`/etc/xdg/reviewbot/config.py`. On Mac OS, the file is
:file:`/Library/Application Support/reviewbot/config.py`.

On Review Bot 3.0 and higher, the location of the configuration file can also
be set through the :envvar:`REVIEWBOT_CONFIG_FILE` environment variable.


.. _worker-configuration-exe-paths:

Paths
-----

.. versionadded:: 3.0

Review Bot will look for executables for the tools in the :envvar:`PATH`
environment variable. However, paths to executables can also be configured
manually using ``exe_paths``. For example:

.. code-block:: python
   :caption: config.py

   exe_paths = {
       'go': '/path/to/go',
       'pmd': '/path/to/pmd',
   }


Some Java-based tools require one or more :file:`.jar` files, which can
also be provided. For example:

.. code-block:: python
   :caption: config.py

   java_classpaths = {
       'checkstyle': ['/path/to/checkstyle.jar'],
   }


.. _worker-configuration-cookies:

Cookie Storage
--------------

.. versionadded:: 3.0

Review Bot needs to store Review Board API cookies somewhere, in order to
maintain an authenticated user session. By default, these cookies will be
stored in one of the following directories, depending on the operating system:

* Linux: ``~/.cache/reviewbot``
* macOS: ``~/Library/Caches/reviewbot``
* Windows (Vista on up):
  ``C:\Users\<username>\AppData\Local\Beanbag\reviewbot\Cache``

The defaults require the user Review Bot is running as to have a home
directory that can be written to.

If needed, an explicit path can be configured by setting ``cookie_dir`` to an
absolute path on the local filesystem. For example:

.. code-block:: python
   :caption: config.py

   cookie_dir = '/opt/reviewbot/data/'

Review Bot will refuse to start up if it can't write cookies to the cookie
directory.


.. _worker-configuration-repositories:

Full Repository Access
----------------------

Some tools require a full clone of the source repository, because they may
need access to all files, not just those which have been changed.

Right now, Review Bot supports full repository access for the following types
of repositories:

* Git
* Mercurial

The worker can define the list of repositories they're allowed to clone.
Your workers don't all need to support the same list of repositories.

Each repository definition supports the following configuration fields:

``name`` (required)
    The configured name of the repository in Review Board.

``type`` (required)
    The repository type:

    * Git: ``git``
    * Mercurial: ``mercurial``

``clone_path`` (required)
    The git or Mercurial URL (possibly including credentials) to clone the
    repository from.

These repositories can be specified in the main Review Bot worker
configuration file, or in a separate JSON file.


.. _worker-configuration-repositories-setting:

1. The Review Bot configuration file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To configure your repositories here, set the ``repositories`` key. For
example:

.. code-block:: python
   :caption: config.py

   repositories = [
       {
           'name': 'Review Board',
           'type': 'git',
           'clone_path': 'https://github.com/reviewboard/reviewboard.git',
       },
       {
           'name': 'Upstream Git',
           'type': 'git',
           'clone_path': 'https://github.com/git/git.git',
       },
       {
           'name': 'Upstream Mercurial',
           'type': 'hg',
           'clone_path': 'https://www.mercurial-scm.org/repo/hg/',
       },
   ]


.. _worker-configuration-repositories-json:

2. Repositories JSON file
^^^^^^^^^^^^^^^^^^^^^^^^^

.. versionadded:: 3.0

You can manage your repositories in a separate JSON file. To do this, set
the ``repositories_config_path`` to the location of your JSON file.

For example:

.. code-block:: python
   :caption: config.py

   repositories_config_path = '/etc/xdg/reviewbot/repositories.json'


.. code-block:: json
   :caption: repositories.json

   [
       {
           "name": "Review Board",
           "type": "git",
           "clone_path": "https://github.com/reviewboard/reviewboard.git"
       },
       {
           "name": "Upstream Git",
           "type": "git",
           "clone_path": "https://github.com/git/git.git"
       },
       {
           "name": "Upstream Mercurial",
           "type": "hg",
           "clone_path": "https://www.mercurial-scm.org/repo/hg/"
       }
   ]


.. _worker-configuration-auto-fetch:

Automatically Fetch Repositories From Review Board
--------------------------------------------------

.. versionadded:: 2.0

If you have many workers and repositories, it may not be feasible to configure
repositories by hand. You can also configure a list of Review Board servers to
fetch lists of repositories from.

.. note::

   Either the repository's :guilabel:`Path` or :guilabel:`Mirror Path` field
   in Review Board must be set to a URL that the Review Bot worker can access
   and clone from.

   If the path is configured to a local file path on the Review Board server,
   and the worker doesn't have local access to that same path (e.g., it's
   running on a different server, and you're not using a shared filesystem
   mount), then you will need to expose the repository over HTTP(S) and set
   :guilabel:`Mirror Path` to that address.

Each server definition supports the following configuration fields:

``url`` (required)
    The URL to the Review Board server. This must be accessible to the
    worker.

``user`` (optional)
    The username used to authenticate with the API.

    This user must have access to the repositories you want to automatically
    configure.

``token`` (optional)
    The :ref:`API token <reviewboard:api-tokens>` used to authenticate with
    the API.

    The token can be set with a read-only access policy.

``user`` and ``token`` are required if anonymous users are unable to access
information on the repositories you want to use (i.e., if
:ref:`anonymous read-only access <reviewboard:auth-general-settings>` is
turned off or the repositories are set up with access control lists in
Review Board).

These servers can be specified in the main Review Bot worker configuration
file, or in a separate JSON file.


.. _worker-configuration-reviewboard-servers-setting:

1. The Review Bot configuration file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To configure your list of servers here, set the ``reviewboard_servers`` key.
For example:

For example:

.. code-block:: python
   :caption: config.py

   reviewboard_servers = [
       {
           'user': 'reviewbot',
           'token': 'dd16b7208a2a8c88be6788c22340ae46823fc57e',
           'url': 'https://reviews1.eng.example.com',
       },
       {
           'url': 'https://reviews2.eng.example.com',
       },
   ]

Be aware that manually configured repositories will override any
automatically fetched configuration of a duplicate repository entry.

.. note:: This setting was renamed in Review Bot 3.0.

   In Review Bot 2.0, this setting was called ``review_board_servers``. For
   consistency, the old setting was deprecated in 3.0, and will be removed in
   4.0.

   See :ref:`upgrading-config-3.0`.


.. _worker-configuration-reviewboard-servers-json:

2. Servers JSON file
^^^^^^^^^^^^^^^^^^^^

.. versionadded:: 3.0

You can manage your list of Review Board servers in a separate JSON file. To
do this, set the ``reviewboard_servers_config_path`` to the location of your
JSON file.

For example:

.. code-block:: python
   :caption: config.py

   reviewboard_servers_config_path = '/etc/xdg/reviewbot/servers.json'


.. code-block:: json
   :caption: servers.json

   [
       {
           "user": "reviewbot",
           "token": "dd16b7208a2a8c88be6788c22340ae46823fc57e",
           "url": "https://reviews1.eng.example.com"
       },
       {
           "url": "https://reviews2.eng.example.com"
       }
   ]
