.. _configuration:

=============
Configuration
=============


.. _extension-configuration:

Extension Configuration
=======================

After the Review Bot extension is enabled, it needs to be configured. Open the
Review Board administration page and click :guilabel:`Extensions` in the top
bar. Under the extension called "Review Bot", click :guilabel:`Configure` to
set up the extension.

There are two items that need to be set here: the user, and the broker URL.

.. image:: extension-configuration.png


Review Bot User
---------------

Review Bot uses a special user account to post reviews. If you were previously
using Review Bot 0.1 or 0.2, select the existing Review Bot user. Otherwise,
click :guilabel:`create a new user for Review Bot`.


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


Tool Configurations
===================

To set up a tool to run, open the Review Board administration page and click
:guilabel:`Integrations` in the top bar. Under the Review Bot section, click
:guilabel:`Add a new configuration`.

.. image:: integrations-list.png

Each tool configuration allows you to specify a tool to run, the conditions for
when that tool is run, and some options for how it is run.

First, give the configuration a name. You can then choose a set of conditions
for when the tool should run. If you would like it to run on every change,
choose :guilabel:`Always match`. Otherwise, you can select a set of conditions
(such as a specific repository, or an assigned review group).

Next, choose which tool to run. Once a tool is selected, additional
tool-specific options may appear.

.. image:: tool-configuration.png

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


Repositories
------------

Some tools require a full clone of the source repository, because they may need
access to all files, not just those which have been changed.

Right now, Review Bot supports full repository access for Git and hg repositories.
This requires configuring each repository on the worker, which allows different
repositories to be spread across different hosts. These are specified in the
worker config file as a list of dictionaries, with three fields. The ``name``
should be the configured name of the repository inside the Review Board admin
interface. The ``type`` should currently be ``git`` or ``hg``, and ``clone_path``
should be set to the git or hg URL (possibly including credentials) to clone the
repository from.

.. code-block:: python

   repositories = [
       {
           'name': 'Review Board',
           'type': 'git',
           'clone_path': 'https://github.com/reviewboard/reviewboard.git',
       },
       {
           'name': 'Git',
           'type': 'git',
           'clone_path': 'https://github.com/git/git.git',
       },
       {
           'name': 'MercurialRockz',
           'type': 'hg',
           'clone_path': 'https://www.mercurial-scm.org/repo/hg/',
       },
   ]
