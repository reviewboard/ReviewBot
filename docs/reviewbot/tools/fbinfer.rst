.. _tool-fbinfer:

=======
FBInfer
=======

.. versionadded:: 3.0

FBInfer_ is a static analysis tool compatible with a large number of
languages, and offering a wide variety of checks.

The following types of projects can be built using FBInfer:

* Android
* Apache Ant
* Buck
* C
* CMake
* Gradle with and without a Wrapper
* iOS
* Java
* Make
* Maven
* Objective-C
* XCode

Unlike many tools, this doesn't operate on individual files.


.. _FBInfer: https://fbinfer.com/


Installation
============

This tool requires FBInfer to be installed on the system running the Review
Bot worker. This is a large dependency, so make sure you have sufficient
storage and RAM available.

See the `FBInfer installation guide`_ for installation instructions.

.. note::

   We **do not recommend** using the FBInfer Docker image with Review Bot.
   FBInfer will be run any time a change is posted or updated, and the
   Docker image is not suitable for this use case.


.. _FBInfer installation guide: https://fbinfer.com/docs/getting-started/


Configuration
=============

FBInfer Location
----------------

Review Bot will try looking for the :command:`infer` command in Review Bot's
:envvar:`PATH` environment variable. If it can't be found, or a different name
is used for this tool (such as :command:`run.sh`), then you'll need to specify
the path in the :ref:`Review Bot worker config file <worker-configuration>`:

.. code-block:: python

    exe_paths = {
        'infer': '/path/to/infer',
    }

You will need to restart the Review Bot worker after making this change.


Enabling Full Repository Access
-------------------------------

This tool requires full repository access, which is available for Git and
Mercurial repositories. Each repository you intend to use must be configured
in the Review Bot worker config file.

See :ref:`worker-configuration-repositories` for instructions.


Preparing Your Build Environment
--------------------------------

Because FBInfer can run static analysis on a wide variety of projects,
the source code will often require numerous external dependencies or
compile-time flags.

Compile-time flags can be specified in the worker configuration (documented
below), but you will need to install any dependencies on the worker.

It's recommended that you set up the worker on a system which is already set
up to build your software in order to ensure that the necessary build
environment is available.


Enabling FBInfer in Review Board
--------------------------------

First, you'll need to add a Review Bot configuration in Review Board (see
:ref:`extension-configuration-tools`).

The following configuration options are available:

:guilabel:`Build system` (required):
    The build system used to compile the project. The following build system
    options are supported:

    :guilabel:`Android/Gradle with Wrapper`:
        Runs :command:`infer run -- ./gradlew`

    :guilabel:`Apache Ant`:
        Runs :command:`infer run -- ant`

    :guilabel:`Buck`
        Runs :command:`infer run -- buck build`

    :guilabel:`Clang (C/Objective-C)`
        Runs :command:`infer run -- clang -c`

    :guilabel:`CMake`
        Runs :command:`infer run -- cmake`

    :guilabel:`Gradle`
        Runs :command:`infer run -- gradle`

    :guilabel:`Java`
        Runs :command:`infer run -- javac`

    :guilabel:`Make`
        Runs :command:`infer run -- make`

    :guilabel:`Maven`
        Runs :command:`infer run -- mvn`

    :guilabel:`XCode`
        Runs :command:`infer run -- xcodebuild`

:guilabel:`Build target` (optional):
    The name of the target to build, if the build system needs one or is
    capable of building multiple targets.

    For XCode, this will use :command:`xcodebuild -target <name>`. For all
    other build systems, the target will be added after the build system
    command above.

:guilabel:`XCode configuration` (optional):
    Any additional configuration options needed for the XCode build.

    This is ignored for non-XCode builds.

    This is equivalent to :command:`xcodebuild -configuration <configuration>`.

:guilabel:`XCode SDK` (optional):
    The name of an SDK to include for XCode configurations.

    This is ignored for non-XCode builds.

    This is equivalent to :command:`xcodebuild -sdk <sdk>`.
