.. _tool-checkstyle:

==========
Checkstyle
==========

checkstyle_ is a static analysis tool that provides a variety of checkers
for Java code and documentation.

.. _checkstyle: https://checkstyle.sourceforge.io/


Supported File Types
====================

The following are supported by this tool:

* Java: :file:`*.java`


Installation
============

To install checkstyle, `download the latest checkstyle.jar`_ file and place
it somewhere on your system.

We recommend choosing a common path for your Review Bot :file:`.jar` files.
Make note of the location. You'll be configuring it below.


.. _download the latest checkstyle.jar:
   https://github.com/checkstyle/checkstyle/releases/


Configuration
=============

Checkstyle Location
-------------------

First, make sure you have :command:`java` in your path, or specified in
:ref:`exe_paths <worker-configuration-exe-paths>`. For example:

.. code-block:: python

   exe_paths = {
       'java': ['/path/to/java'],
   }

You'll then need to :ref:`specify the path <worker-configuration-exe-paths>`
to the downloaded :file:`checkstyle.jar` file in the :ref:`Review Bot worker
config file <worker-configuration>`:

.. code-block:: python

   java_classpaths = {
       'checkstyle': ['/path/to/checkstyle.jar'],
   }

You will need to restart the Review Bot worker after making this change.


Enabling Checkstyle in Review Board
-----------------------------------

First, you'll need to add a Review Bot configuration in Review Board (see
:ref:`extension-configuration-tools`).

The following configuration options are available:

:guilabel:`Configuration XML` (required):
    You'll need to provide either:

    1. The name of an existing `Checkstyle-provided XML configuration`_
       (such as ``google_checks.xml`` or ``sun_checks.xml``)
    2. The full contents of a custom configuration XML file (see
       the `XML configuration documentation`_ for details)

.. _Checkstyle-provided XML configuration:
   https://checkstyle.sourceforge.io/style_configs.html
.. _XML configuration documentation:
   https://checkstyle.sourceforge.io/config.html
