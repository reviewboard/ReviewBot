.. _installation-docker:

========================
Review Bot Docker Images
========================

.. versionadded:: 3.0

Review Bot can be installed through our official Docker images, helping you
quickly get your infrastructure set up with minimal effort.

Each release ships with a set of pre-made tool pack images that check certain
languages. You can also create your own custom Review Bot images that contain
just the tools you need. This is all covered below.


Getting Started
===============

We'll walk you through the basics of setting up Review Bot on Docker in two
different ways:

1. Launching the Review Bot image itself using :ref:`docker run
   <installation-docker-run>`.

2. Launching the image along with a database, web server, and memcached
   using :ref:`docker-compose <installation-docker-compose>`.

You'll also see how you can build a Docker image for just the tools you need.


Before You Begin
----------------

Plan Your Infrastructure
~~~~~~~~~~~~~~~~~~~~~~~~

Review Bot requires a `compatible message broker`_.

RabbitMQ_ is most commonly used, and is available through the `rabbitmq Docker
image`_. This is what we'll use for this guide.


.. _compatible message broker:
   https://docs.celeryproject.org/en/stable/getting-started/backends-and-brokers/index.html
.. _RabbitMQ: http://www.rabbitmq.com/
.. _rabbitmq Docker image: https://hub.docker.com/_/rabbitmq


Choose a Version and Tool Packs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Our Docker images are available in the following forms:

* :samp:`beanbag/reviewbot-{pack}:latest`
  -- The latest stable release of Review Bot for a given language/tool pack.
* :samp:`beanbag/reviewbot-{pack}:{X}`
  -- The latest stable release in a major version series (e.g., 3).
* :samp:`beanbag/reviewbot-{pack}:{X.Y}`
  -- The latest stable release in a major.minor version series (e.g., 3.0).
* :samp:`beanbag/reviewbot-{pack}:{X.Y.Z}`
  -- A specific release of Review Bot (e.g., 3.0.1).

.. note::

   We recommend using a ``{X.Y}``-versioned image, rather than using
   ``latest``, to help avoid unexpected changes with future versions. You'll
   still benefit from bug fixes.

You can choose any of the following tool pack images:

* :docker:`beanbag/reviewbot-c`

  * :ref:`tool-clang`
  * :ref:`tool-cppcheck`
  * :ref:`tool-cpplint`

* :docker:`beanbag/reviewbot-go`

  * :ref:`tool-gofmt`
  * :ref:`tool-gotool`

* :docker:`beanbag/reviewbot-java`

  * :ref:`tool-checkstyle`

* :docker:`beanbag/reviewbot-javascript`

  * :ref:`tool-jshint`

* :docker:`beanbag/reviewbot-python`

  * :ref:`tool-doc8`
  * :ref:`tool-flake8`
  * :ref:`tool-pycodestyle`
  * :ref:`tool-pydocstyle`
  * :ref:`tool-pyflakes`

* :docker:`beanbag/reviewbot-ruby`

  * :ref:`tool-rubocop`

* :docker:`beanbag/reviewbot-rust`

  * :ref:`tool-cargotool`
  * :ref:`tool-rustfmt`

* :docker:`beanbag/reviewbot-shell`

  * :ref:`tool-shellcheck`

* :docker:`beanbag/reviewbot-fbinfer`

  * :ref:`tool-fbinfer`

* :docker:`beanbag/reviewbot-pmd`

  * :ref:`tool-pmd`


Using Docker Run
----------------

First, make sure you have RabbitMQ_ (or another compatible message broker)
configured and ready for Review Bot. You can use an existing Docker image or
:ref:`install a broker manually <installation-manual-message-broker>`.

To start a new container, run:

.. code-block:: console

   $ docker pull beanbag/reviewbot-<pack>:X.Y.Z
   $ docker run -P \
         --name <name> \
         -v <local_path>:/config \
         -v <local_path>:/repos \
         -e BROKER_URL=<broker URL> \
         beanbag/reviewbot-<pack>:X.Y.Z


For example:

.. code-block:: console

   $ docker pull beanbag/reviewbot-python:3.0
   $ docker run -P \
         --name <name> \
         -v /etc/reviewbot/config:/config \
         -v /var/lib/reviewbot/repos:/repos \
         -e BROKER_URL=amqp://reviewbot:reviewbot123@rabbitmq/reviewbot \
         beanbag/reviewbot-python:3.0


We'll go over the settings later.


Using Docker Compose
--------------------

:command:`docker-compose` can help you define and launch all the services
needed for your Review Bot deployment.

A simple :file:`docker-compose.yaml` for launching RabbitMQ and two Review
Bot workers (one for Python, one for Go) might look like:

.. code-block:: yaml
   :caption: docker-compose.yaml

   version: '3.7'

   services:
     rabbitmq:
       image: rabbitmq:3-management
       restart: always
       hostname: rabbitmq
       environment:
         - RABBITMQ_DEFAULT_VHOST=reviewbot
         - RABBITMQ_DEFAULT_USER=reviewbot
         - RABBITMQ_DEFAULT_PASS=reviewbot123
         - RABBITMQ_ERLANG_COOKIE=secret-dont-tell
       volumes:
         - /var/lib/reviewbot/rabbitmq/data:/var/lib/rabbitmq/
         - /var/log/reviewbot/rabbitmq:/var/log/rabbitmq
       ports:
         - 15672:15672
         - 5672:5672
       healthcheck:
         test: ['CMD', 'rabbitmqctl', 'status']
         interval: 5s
         timeout: 20s
         retries: 5

     reviewbot-go:
       image: beanbag/reviewbot-go:3.0
       restart: always
       depends_on:
         rabbitmq:
           condition: service_healthy
       environment:
         - BROKER_URL=amqp://reviewbot:reviewbot123@rabbitmq/reviewbot
       volumes:
         - /etc/reviewbot/config:/config
         - /var/lib/reviewbot/repos:/repos


     reviewbot-python:
       image: beanbag/reviewbot-python:3.0
       restart: always
       depends_on:
         rabbitmq:
           condition: service_healthy
       environment:
         - BROKER_URL=amqp://reviewbot:reviewbot123@rabbitmq/reviewbot
       volumes:
         - /etc/reviewbot/config:/config
         - /var/lib/reviewbot/repos:/repos


You'll want to tailor this to your configuration and security requirements.
This is purely for demonstrative purposes.

To bring up the environment, run:

.. code-block:: console

   $ docker-compose up

You can then enable Review Bot in Review Board and point it to the broker
URL for your server.

.. note::

   Make sure to use the publicly-resolvable domain and exposed RabbitMQ port
   for the server running this Docker environment)! The internal broker URLs
   shown above are only valid within the Docker environment.


Configuration
=============

Repository Volumes
------------------

There are two volume mounts available: :file:`/config` and :file:`/repos`.

These are only required if using tools that require :ref:`full repository
access <worker-configuration-repositories>`.

:file:`/config` is a directory that may contain any of the following files:

* :ref:`repositories.json <worker-configuration-repositories-json>`
  -- A list of repositories Review Bot can pull from
* :ref:`servers.json <worker-configuration-reviewboard-servers-json>`
  -- A list of Review Board servers that Review Bot can query for available
  repositories


Broker Configuration
--------------------

The URL for the broker must be provided by passing ``BROKER_URL``.

For RabbitMQ, this is in the form of:
``amqp://<username>:<password>@<host>/<queue-vhost>``.

See :ref:`extension-configuration-broker-url` for more information.


Custom Review Bot Images
========================

You can build your own custom Review Bot images featuring just the tools
you need to install:

1. Determine the tools you want to use. The following tool IDs can be
   specified:

   * :ref:`checkstyle <tool-checkstyle>`
   * :ref:`clang <tool-clang>`
   * :ref:`cppcheck <tool-cppcheck>`
   * :ref:`cpplint <tool-cpplint>`
   * :ref:`doc8 <tool-doc8>`
   * :ref:`fbinfer <tool-fbinfer>`
   * :ref:`flake8 <tool-flake8>`
   * :ref:`gofmt <tool-gofmt>`
   * :ref:`gotool <tool-gotool>`
   * :ref:`jshint <tool-jshint>`
   * :ref:`pmd <tool-pmd>`
   * :ref:`pycodestyle <tool-pycodestyle>`
   * :ref:`pydocstyle <tool-pydocstyle>`
   * :ref:`pyflakes <tool-pyflakes>`
   * :ref:`rubocop <tool-rubocop>`
   * :ref:`rustfmt <tool-rustfmt>`
   * :ref:`shellcheck <tool-shellcheck>`

   .. note::

      Built-in tools will always be installed. Currently, that just includes
      :ref:`tool-rbsecretscanner`.

2. Create a :file:`Dockerfile` containing the following:

   .. code-block:: dockerfile

      # Specify your tool IDs from above here:
      ARG TOOLS="tool1 tool2 tool3"

      FROM beanbag/reviewbot:<version>

3. Build the image:

   .. code-block:: console

      $ docker build -t my-reviewbot .

   See the `docker build documentation`_ for more information on this command.

4. Launch a container from your new image:

   .. code-block:: console

      $ docker run \
          -P \
          --name ... \
          -v ... \
          -e ... \
          my-reviewbot


.. _docker build documentation:
   https://docs.docker.com/engine/reference/commandline/build/
