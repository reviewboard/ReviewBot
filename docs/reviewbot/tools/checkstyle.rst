.. _tool-checkstyle:

==========
checkstyle
==========

checkstyle_ is a static analysis tool that provides a variety of checkers
for java code.

.. _checkstyle: http://checkstyle.sourceforge.net/


Installation
============

checkstyle can be installed through many system package managers, or
downloaded and installed manually.


Configuration
=============

Because there are a variety of methods to install checkstyle, there's
no consistent location (or name) of the JAR file.

The path and name of the JAR file has to be configured in the
:ref:`Review Bot worker config file <worker-configuration>`.

Also it is required that "java" is in your path.

.. code-block:: python

    checkstyle_path = '/opt/checkstyle.jar'
