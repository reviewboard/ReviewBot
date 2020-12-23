.. _tool-fbinfer:

=======
FBInfer
=======

`FBInfer`_ is a static analysis tool that can compile a wide range of projects
and produce a list of potential bugs. These bugs can then be intercepted
before they have shipped to users, preventing crashes and poor performance in
production. The types of projects that can be used with FBInfer include but
are not limited to:

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

.. _FBInfer: https://fbinfer.com/


Installation
============

This tool requires that FBInfer is installed on the system running the Review
Bot worker. FBInfer is available through Homebrew (Mac only), as a binary
release (for Linux or Mac users that do not wish to use Homebrew) and
alternatively as a Docker image. More information about `installation`_ can be
found on the official FBInfer website.

.. _installation: https://fbinfer.com/docs/getting-started/


Configuration
=============

This tool requires full repository access, which is available for Git and
Mercurial repositories. Each repository you intend to use must be configured
in the Review Bot worker config file. See :ref:`worker-configuration` for more
details.

Because FBInfer can run static analysis on a wide variety of projects,
the source code will often require numerous external dependencies or
compile-time flags. The tool configuration allows you to specify additional
command line arguments that will be passed to :command:`infer`. It's
recommended that you set up the worker on a system which is already set up
to build your software in order to ensure that the necessary build environment
is available.
