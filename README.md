Review Bot
==========

Review Bot is a tool for automating tasks on code uploaded to
[Review Board](https://www.reviewboard.org/), and posting the results as a code
review. Review Bot was built to automate the execution of static analysis
tools.

Review Bot is:

* **Extensible:** Writing plugins is simple using a convenient API to
retrieve code files and craft a review. If more power is needed, tools
can access the full Review Board API.

* **Scalable:** Review Bot is built using
[Celery](http://www.celeryproject.org/) and can scale out to service
very large Review Board instances.

* **Integrated Configuration:** Tools are configured through the
Review Board admin panel, including settings uniquely defined for each
task.


Installation
============

Review Bot requires installation of a Review Board extension, a message broker,
and at least one Review Bot worker.


Message Broker
--------------

[RabbitMQ](http://www.rabbitmq.com/) is the recommended message broker.
Although Review Bot is tested with RabbitMQ, any of the Celery
[supported brokers](http://docs.celeryproject.org/en/latest/getting-
started/brokers/) *should* work.

Please see the broker specific documentation for installation
instructions.


Review Board Extension
----------------------

Review Bot 1.0 is a fairly major departure from the previous pre-releases (0.1
and 0.2), and *requires Review Board 3.0 or newer*. If you're using an older
version of Review Board, please see the documentation for the 0.1 or 0.2
branches.

If you're updating from a previous version of Review Bot, you'll need to
uninstall the old extension module first. The configuration of the old
extension works somewhat differently than it used to, so you may want to first
make a note of which tools are used and what their configuration is. You can
then uninstall the old version by running:

```sh
pip uninstall Review_Bot_Extension
```

To install the Review Bot extension, on the Review Board server, run:

```sh
pip install reviewbot-extension
```

Once done, reload Apache, then log in to Review Board's administration
interface and select "Extensions" at the top of the page. If you don't see the
"Review Bot" extension, click "Scan for installed extensions". Click "Enable"
on the extension to enable it.


Workers
-------

If you had previously installed Review Bot 0.1 or 0.2, you'll need to uninstall
the old worker first:

```sh
pip uninstall ReviewBot
```

To install the worker, run:

```sh
pip install reviewbot-worker
```

The worker can be started using the `reviewbot` command:

```sh
reviewbot worker -b <broker_url>
```

This will start up the worker, which is a celery app. For more info on this
process, see the documentation on
[Celery Applications](http://docs.celeryproject.org/en/latest/userguide/application.html)
and [Workers](http://docs.celeryproject.org/en/latest/userguide/workers.html).


Tools
-----

When a worker starts, it will check to see what tools are available. Installing
the Review Bot worker will automatically install tools which are written in
Python, but some other tools require separate installation.

The available tools are:

* BuildBot "try"

  This tool will attempt to build the patch using the BuildBot "try" command".
  The necessary dependencies for buildbot are automatically installed along
  with the worker.

* CPPCheck, a tool for static C/C++ code analysis

  CPPCheck is available through most system package managers. For example, on
  Ubuntu:

  ```sh
  sudo apt-get install cppcheck
  ```

* CPPLint, static code checker for C++

  The necessary dependencies for CPPLint are automatically installed with
  the worker.

* JSHint, a JavaScript code quality tool

  JSHint is available through npm. This requires nodejs to be installed on the
  system:

  ```sh
  sudo npm install -g jshint
  ```

* PEP-8, the Python style guide checker

  The necessary dependencies for PEP-8 are automatically installed with the
  worker.

* PMD

  PMD can be installed through many system package managers, or downloaded and
  installed manually. Using PMD requires the path to the PMD executable (often
  called `run.sh`) to be configured. See "Worker Configuration" below.

* Pyflakes, a passive checker of Python programs

  The necessary dependencies for Pyflakes are automatically installed with the
  worker.


Configuration
=============

Extension Configuration
-----------------------

After the Review Bot extension is enabled, it needs to be configured. On the
Review Bot entry in the extension list, click on "Configure".

There are two items that need to be set here: the user, and the broker URL. If
you were previously using Review Bot 0.1 or 0.2, select the existing Review Bot
user. Otherwise, click "create a new user for Review Bot".

For the broker URL, put in the URL of your RabbitMQ or other celery broker.

After saving the configuration, the page will attempt to contact the broker and
check for workers. The "Broker Status" box will indicate whether everything is
set up correctly.


Worker Configuration
--------------------

In most cases, the worker does not require any configuration. When you start
the Review Bot worker it will print a message, "Loading config file", with the
path to the configuration file. If you need to configure the worker, create
this file.

At the moment, the only configuration necessary is if you want to use the PMD
tool, which requires configuration of the path to the PMD executable (because
PMD does not have a standard installation procedure). The path should be set to
the location of PMD's run script, which is sometimes called `pmd` and sometimes
called `run.sh`, depending on the method of installation.

```python
pmd_path = '/usr/local/bin/pmd'
```


Tool Configurations
-------------------

Once the extension itself has been configured, you need to add one or more tool
configurations. In the admin site, "Integrations" at the top. Then click "Add a
new configuration" under the Review Bot section.

Each tool configuration allows you to specify a tool to run, the conditions for
when that tool is run, and some options for how it is run.

First, give the configuration a name. You can then choose a set of conditions
for when the tool should run. If you would like it to run on every change,
choose "Always match". Otherwise, you can select a set of conditions (such as
a repository, or an assigned group).

Next, choose which tool to run. It's important to note that the tools will only
run if they're currently available on a running worker node. Finally, you can
set a handful of tool-specific options.

You can configure the same tool multiple times via multiple configurations.
This is useful in cases where you might have two different groups that have
different needs. Note that if the conditions for two configurations of the same
tool both match, the tool will run twice.
