.. _installation:

============
Installation
============

Requirements
============

Review Bot 1.0 is supported for *Review Board 3.0 beta 1 and newer*. If you're
using an older version of Review Board, please see the documentation for the
`0.1 <https://github.com/reviewboard/ReviewBot/blob/release-0.1.x/README.md>`_
or `0.2
<https://github.com/reviewboard/ReviewBot/blob/release-0.2.x/README.md>`_
branches.

A Review Bot setup consists of three pieces: the Review Bot extension for
Review Board, a message broker, and at least one Review Bot worker.


Review Board Extension
======================

Review Bot 1.0 is a fairly major departure from the previous pre-releases, and
*requires Review Board 3.0*.

If you're updating from a previous version of Review Bot, you'll need to
uninstall the old extension module first. The configuration of the old
extension works somewhat differently than it used to, so you may want to first
make a note of which tools are used and what their configuration is. You can
then uninstall the old version by running::

    $ sudo pip uninstall Review_Bot_Extension

The Review Bot extension can then be installed by running::

    $ sudo pip install reviewbot-extension

Depending on your configuration, you may need to restart or reload your web
server. The specific command depends on your individual setup, but is usually
something like the following::

    $ sudo service httpd reload

Now open the Review Board administration page, and click :guilabel:`Extensions`
in the top bar. You should see a new extension called "Review Bot". Click
:guilabel:`Enable` to enable it.

.. image:: extensions-list.png

Once installed, the Review Bot extension requires some
:ref:`configuration <extension-configuration>`.


Message Broker
==============

Review Bot uses a message broker to distribute worker tasks. The message broker
can be installed on the Review Board server or on another system, depending on
your needs. `RabbitMQ`_ is the recommended message broker, though any of
Celery's :ref:`supported brokers <celery:brokers>` should work.

.. _RabbitMQ: http://www.rabbitmq.com/


Review Bot Worker
=================

The Review Bot worker can be installed on the Review Board server or on another
system, depending on your needs.

If you had previously installed Review Bot 0.1 or 0.2, you'll need to uninstall
the old worker first::

    $ sudo pip uninstall ReviewBot

To install the Review Bot worker, run::

    $ sudo pip install reviewbot-worker


Starting the Worker
-------------------

Once the worker is installed and your message broker is running, you can start
the worker node. This is done via the following command (replacing
:samp:`<broker_url>` with the URL to your message broker)::

    $ reviewbot worker -b <broker_url>


Additional Tool Dependencies
============================

Many Review Bot tools will install the needed dependencies automatically, but
some will require manual installation of additional components. See the
individual documentation for each tool for installation requirements and
instructions.


Running the Review Bot Worker
=============================

To start the worker process, run :command:`reviewbot worker -b broker_url`
(where ``broker_url`` is the URL of your RabbitMQ or other message broker).
It's recommended to set this up to run as a service when the server boots. See
the documentation on `daemonizing celery`_ for more details.

.. _daemonizing celery: https://docs.celeryproject.org/en/latest/userguide/daemonizing.html
