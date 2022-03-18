.. _reviewbot-coderef:

==========================
Module and Class Reference
==========================

Base Tools Support
==================

.. autosummary::
   :toctree: worker

   reviewbot.tools.base
   reviewbot.tools.base.mixins
   reviewbot.tools.base.registry
   reviewbot.tools.base.tool


Unit Testing
============

.. autosummary::
   :toctree: worker

   reviewbot.testing.testcases
   reviewbot.testing.utils
   reviewbot.tools.testing
   reviewbot.tools.testing.decorators
   reviewbot.tools.testing.testcases


Reviews, Patches, and Commenting
================================

.. autosummary::
   :toctree: worker

   reviewbot.processing.review


Utilities
=========

.. autosummary::
   :toctree: worker

   reviewbot.utils.api
   reviewbot.utils.filesystem
   reviewbot.utils.log
   reviewbot.utils.process
   reviewbot.utils.text


Worker Operations
=================

.. autosummary::
   :toctree: worker

   reviewbot.celery
   reviewbot.config
   reviewbot.deprecation
   reviewbot.errors
   reviewbot.repositories
   reviewbot.tasks


Built-in Tools
==============

.. autosummary::
   :toctree: worker

   reviewbot.tools.cargotool
   reviewbot.tools.checkstyle
   reviewbot.tools.clang
   reviewbot.tools.cppcheck
   reviewbot.tools.cpplint
   reviewbot.tools.doc8
   reviewbot.tools.fbinfer
   reviewbot.tools.flake8
   reviewbot.tools.gofmt
   reviewbot.tools.gotool
   reviewbot.tools.jshint
   reviewbot.tools.pmd
   reviewbot.tools.pycodestyle
   reviewbot.tools.pydocstyle
   reviewbot.tools.pyflakes
   reviewbot.tools.rbsecretscanner
   reviewbot.tools.rubocop
   reviewbot.tools.rustfmt
   reviewbot.tools.shellcheck
