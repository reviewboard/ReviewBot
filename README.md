Review Bot
==========

Review Bot is a tool for automating tasks on code uploaded to a
[Review Board](http://www.reviewboard.org/) instance, and posting the
results as a code review. Review Bot was built to automate the
execution of static analysis tools, for a list of tools Review Bot supports,
please see the
[Supported Tools](https://github.com/smacleod/ReviewBot/wiki/Supported-Tools)
wiki page.

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

Review Bot requires installation of a Review Board extension, a
message broker, and at least one Review Bot worker.


Message Broker
--------------

[RabbitMQ](http://www.rabbitmq.com/) is the recommended message
broker. Although Review Bot is tested with RabbitMQ, any of the Celery
[supported brokers](http://docs.celeryproject.org/en/latest/getting-
started/brokers/) *should* work.

Please see the broker specific documentation for installation
instructions.

Review Board Extension
----------------------

*Review Bot requires a version 1.7 Review Board installation.*

To install Review Bot's Review Board extension, clone this repository
and install with the following commands:

    git clone git://github.com/smacleod/ReviewBot.git
    cd ReviewBot/extension
    python setup.py install

After installation the 'Review-Bot-Extension' should be enabled and
configured in Review Board's admin panel. Please see the [Celery
documentation](http://docs.celeryproject.org/en/latest/getting-started/brokers/)
for help configuring the 'Broker URL'.

Workers
-------

*The Review Bot worker requires the
[master development branch](https://github.com/reviewboard/rbtools/)
of rbtools*

To install the Review Bot worker to a server, clone this repository
and install with the following commands:

    git clone git://github.com/smacleod/ReviewBot.git
    cd ReviewBot/bot
    python setup.py install

The worker can be started using the `reviewbot` command:

    reviewbot worker -b <broker_url>

`reviewbot` starts an instance of the `celery` command using Review
Bot's 'app'. For more information please see documentation
on [Celery Application's](http://docs.celeryproject.org/en/latest/userguide/application.html)
and [Workers](http://docs.celeryproject.org/en/latest/userguide/workers.html).

CPPCheck
--------
To use the cppcheck plugin - you must ensure that cppcheck is available on the worker machine.

To install on Ubuntu run:

    sudo apt-get install cppcheck

For other distributions or Windows, please see http://sourceforge.net/projects/cppcheck/

Installing and Registering Tools
--------------------------------

Workers are able to find installed tools using
[Entry Points](http://packages.python.org/distribute/pkg_resources.html#entry-points).
New tool classes should add a `reviewbot.tools` entry point. The entry
point for the pep8 tool is part of the review bot installation, here
is an example showing its definition:

    'reviewbot.tools': [
            'cppcheck = reviewbot.tools.cppcheck:CPPCheckTool',
            'cpplint = reviewbot.tools.cpplint:CPPLintTool',
            'pep8 = reviewbot.tools.pep8:PEP8Tool',
    ],

After a tool has been installed on a worker, it must be registered
with the Review Bot extension, and configured in the admin panel.
Registering tools is accomplished in the following manner:

  1. Go to the extension list in the admin panel.
  2. Click the 'DATABASE' button for the 'Review-Bot-Extension'.
  3. Click the 'Review bot tools' link.
  4. Click 'REFRESH INSTALLED TOOLS' in the upper right of the page.

This will trigger tool registration for all of the currently running
workers, and refresh the page. You will now see the list of installed
tools and may configure them using this admin panel.
