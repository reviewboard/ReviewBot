.. _tool-pmd:

===
PMD
===

PMD_ is a static analysis tool that provides a variety of checkers for many
languages.

.. _PMD: https://pmd.github.io/


Supported Versions
==================

Review Bot supports both the 6.x and 7.x major versions of PMD.


Supported File Types
====================

The following are supported by this tool:

* Apex: :file:`*.cls`
* C/C++: :file:`*.c`, :file:`*.cc`, :file:`*.cpp`, :file:`*.cxx`,
  :file:`*.C`, :file:`*.h`, :file:`*.hpp`, :file:`*.hxx`
* C#: :file:`*.cs`
* Dart: :file:`*.dart`
* Fortran: :file:`*.f`, :file:`*.f66`, :file:`*.f77`, :file:`*.f90`,
  :file:`*.for`
* Go: :file:`*.go`
* Groovy: :file:`*.groovy`
* Java: :file:`*.java`
* JavaScript: :file:`*.js`
* Java Server Pages: :file:`*.jsp`, :file:`*.jspf`, :file:`*.jspx`,
  :file:`*.tag`
* Kotlin: :file:`*.kt`
* Lua: :file:`*.lua`
* Matlab: :file:`*.m`
* Modelica: :file:`*.mo`
* Objective-C: :file:`*.h`, :file:`*.m`
* Perl: :file:`*.plm`, :file:`*.pm`, :file:`*.t`
* PHP: :file:`*.class`, :file:`*.php`
* PL/SQL: :file:`*.fnc`, :file:`*.pkb`, :file:`*.pkh`, :file:`*.pks`,
  :file:`*.plb`, :file:`*.pld`, :file:`*.plh`, :file:`*.pls`, :file:`*.prc`,
  :file:`*.sql`, :file:`*.tpb`, :file:`*.tps`, :file:`*.trg`, :file:`*.tyb`,
  :file:`*.typ`
* Python: :file:`*.py`
* Ruby: :file:`*.cgi`, :file:`*.class`, :file:`*.rb`
* Scala: :file:`*.scala`
* Swift: :file:`*.swift`
* VisualForce: :file:`*.component`, :file:`*.page`
* VM: :file:`*.vm`
* XML: :file:`*.xml`

It may also scan other file extensions to see if they appear to be one of the
languages above.

PMD can be configured to match only specific file types.


..
  File Extension References:

  * Apex: https://github.com/pmd/pmd/blob/master/pmd-apex/src/main/java/net/sourceforge/pmd/cpd/ApexLanguage.java
  * C/C++: https://github.com/pmd/pmd/blob/master/pmd-cpp/src/main/java/net/sourceforge/pmd/cpd/CPPLanguage.java
  * C#: https://github.com/pmd/pmd/blob/master/pmd-cs/src/main/java/net/sourceforge/pmd/cpd/CsLanguage.java
  * Dart: https://github.com/pmd/pmd/blob/master/pmd-dart/src/main/java/net/sourceforge/pmd/cpd/DartLanguage.java
  * Fortran: https://github.com/pmd/pmd/blob/master/pmd-fortran/src/main/java/net/sourceforge/pmd/cpd/FortranLanguage.java
  * Go: https://github.com/pmd/pmd/blob/master/pmd-go/src/main/java/net/sourceforge/pmd/cpd/GoLanguage.java
  * Groovy: https://github.com/pmd/pmd/blob/master/pmd-groovy/src/main/java/net/sourceforge/pmd/cpd/GroovyLanguage.java
  * Java: https://github.com/pmd/pmd/blob/master/pmd-java/src/main/java/net/sourceforge/pmd/cpd/JavaLanguage.java
  * Java Server Pages: https://github.com/pmd/pmd/blob/master/pmd-jsp/src/main/java/net/sourceforge/pmd/cpd/JSPLanguage.java
  * Kotlin: https://github.com/pmd/pmd/blob/master/pmd-kotlin/src/main/java/net/sourceforge/pmd/cpd/KotlinLanguage.java
  * Lua: https://github.com/pmd/pmd/blob/master/pmd-lua/src/main/java/net/sourceforge/pmd/cpd/LuaLanguage.java
  * Matlab: https://github.com/pmd/pmd/blob/master/pmd-matlab/src/main/java/net/sourceforge/pmd/cpd/MatlabLanguage.java
  * Modelica: https://github.com/pmd/pmd/blob/master/pmd-modelica/src/main/java/net/sourceforge/pmd/cpd/ModelicaLanguage.java
  * Objective-C: https://github.com/pmd/pmd/blob/master/pmd-objectivec/src/main/java/net/sourceforge/pmd/cpd/ObjectiveCLanguage.java
  * Perl: https://github.com/pmd/pmd/blob/master/pmd-perl/src/main/java/net/sourceforge/pmd/cpd/PerlLanguage.java
  * PHP: https://github.com/pmd/pmd/blob/master/pmd-php/src/main/java/net/sourceforge/pmd/cpd/PHPLanguage.java
  * PL/SQL: https://github.com/pmd/pmd/blob/master/pmd-plsql/src/main/java/net/sourceforge/pmd/cpd/PLSQLLanguage.java
  * Python: https://github.com/pmd/pmd/blob/master/pmd-python/src/main/java/net/sourceforge/pmd/cpd/PythonLanguage.java
  * Ruby: https://github.com/pmd/pmd/blob/master/pmd-ruby/src/main/java/net/sourceforge/pmd/cpd/RubyLanguage.java
  * Scala: https://github.com/pmd/pmd/blob/master/pmd-scala-modules/pmd-scala-common/src/main/java/net/sourceforge/pmd/cpd/ScalaLanguage.java
  * Swift: https://github.com/pmd/pmd/blob/master/pmd-swift/src/main/java/net/sourceforge/pmd/cpd/SwiftLanguage.java
  * VisualForce: https://github.com/pmd/pmd/blob/master/pmd-visualforce/src/main/java/net/sourceforge/pmd/cpd/VfLanguage.java
  * VM: https://github.com/pmd/pmd/blob/master/pmd-vm/src/main/java/net/sourceforge/pmd/lang/vm/VmLanguageModule.java
  * XML: https://github.com/pmd/pmd/blob/master/pmd-xml/src/main/java/net/sourceforge/pmd/xml/cpd/XmlLanguage.java


Installation
============

PMD can be installed through many system package managers, or downloaded and
installed manually.


Configuration
=============

PMD Location
------------

Because there are a variety of methods to install PMD, there's no consistent
location (or name) of the PMD executable. If installed through a package
manager, it can often be invoked via :command:`pmd`. If installed manually,
it's invoked via :command:`run.sh`.

If it's not named :command:`pmd`, or can't be found in Review Bot's
:envvar:`PATH` environment variable, then you'll need to specify the path
in the :ref:`Review Bot worker config file <worker-configuration>`:

.. code-block:: python

    exe_paths = {
        'pmd': '/path/to/pmd',
    }

You will need to restart the Review Bot worker after making this change.


.. note:: This setting was renamed in Review Bot 3.0.

   In Review Bot 2.0, this setting was called ``pmd_path``. For consistency,
   the old setting was deprecated in 3.0, and will be removed in 4.0.

   See :ref:`upgrading-config-3.0`.


Enabling PMD in Review Board
----------------------------

First, you'll need to add a Review Bot configuration in Review Board (see
:ref:`extension-configuration-tools`).

The following configuration options are available:

:guilabel:`Rulesets` (required):
    This can be one of the following:

    1. A comma-separated list of `PMD rulesets`_ to apply (equivalent to
       :command:`pmd -rulesets ...`).

    2. A full `PMD ruleset configuration file`_ (starting with
       ``<?xml ...?>``).

:guilabel:`Scan files` (optional):
    A comma-separated list of file extensions to scan. Only files in the diff
    that match these file extensions will trigger the PMD configuration.

    If not provided, the tool will be ran for all files in the diff.

    For example: ``c,js,py``


.. _PMD rulesets: https://pmd.github.io/latest/pmd_rules_java.html
.. _PMD ruleset configuration file:
   https://pmd.github.io/latest/pmd_userdocs_making_rulesets.html
