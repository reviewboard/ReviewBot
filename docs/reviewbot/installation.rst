.. _installation:

============
Installation
============

If you're upgrading from a previous release, see the instructions on
:ref:`upgrading Review Bot <upgrading>`.


Overview
========

Review Bot |version| supports Review Board 3.0 or 4.0, and Python 2.7 or
3.6 through 3.9.

A Review Bot setup consists of three pieces:

1. The Review Bot extension for Review Board
2. A message broker (such as RabbitMQ_)
3. At least one Review Bot worker (either on the Review Board server or
   somewhere else in your network)


Installing the Review Board Extension
=====================================

To install the Review Bot extension for Review Board, run::

    $ sudo pip install reviewbot-extension

(If you're installing in a virtual environment, don't use ``sudo``.)

Depending on your configuration, you may need to restart or reload your web
server. The specific command depends on your individual setup, but is usually
something like the following::

    $ sudo service httpd reload

Now open the Review Board administration page, and click :guilabel:`Extensions`
in the top bar. You should see a new extension called "Review Bot". Click
:guilabel:`Enable` to enable it.

Once installed, the Review Bot extension requires some
:ref:`configuration <extension-configuration>`.


Install a Message Broker
========================

Review Bot uses a message broker to distribute worker tasks. It's how the
Review Bot extension on Review Board talks to each worker.

The message broker can be installed on the Review Board server or on another
system, depending on your needs. RabbitMQ_ is the recommended message broker,
though any of Celery's :ref:`supported brokers <celery:brokers>` should work.
Refer the broker's documentation for installation instructions.

.. _RabbitMQ: http://www.rabbitmq.com/


Install Review Bot Workers
==========================

A Review Bot worker can be installed on the Review Board server or on
another system, depending on your needs. You can even install multiple workers
on different systems, if you need to scale out further.

To install the main worker package on a server, run::

    $ sudo pip install reviewbot-worker

(If you're installing in a virtual environment, don't use ``sudo``.)

Depending on the tools you need, you may have to install other system packages
or Python packages. Refer to the :ref:`list of tools <tools>` for further
information on setting these up.

As a shortcut, all built-in Python code/doc checking tools can be installed by
running::

    $ sudo pip install reviewbot-worker[all]


Starting the Worker
-------------------

Once the worker is installed and your message broker is running, you can start
the worker node. This is done via the following command (replacing
:samp:`<broker_url>` with the URL to your message broker)::

    $ reviewbot worker -b <broker_url>

It's recommended to set this up to run as a service when the server boots. See
the documentation on `daemonizing celery`_ for more details.

.. _daemonizing celery: https://docs.celeryproject.org/en/latest/userguide/daemonizing.html
