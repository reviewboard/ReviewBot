Review Bot
==========

Review Bot is a tool for automating tasks on code uploaded to a
[Review Board](http://www.reviewboard.org/) instance, and posting the
results as a code review. Review Bot was built to automate the
execution of static analysis tools, and comes with a plugin for
automatically analyzing Python code using the
[pep8](http://pypi.python.org/pypi/pep8/) Python style guide checker.

* **Extensible:** Writing plugins is simple using a convenient API to
retrieve code files and craft a review. If more power is needed, tools
can access the full Review Board API.

* **Scalable:** Review Bot is built using
[Celery](http://www.celeryproject.org/) and can scale out to service
very large Review Board instances.

* **Integrated Configuration:** Tasks are configured through the
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
and install with easy_install:

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
[api development branch](https://github.com/reviewboard/rbtools/tree/api)
of rbtools*

To install the Review Bot worker to a server, clone this repository
and install with easy_install:

    git clone git://github.com/smacleod/ReviewBot.git
    cd ReviewBot/bot
    python setup.py install

The worker can be started using the 'reviewbot' command:

    reviewbot worker -b <broker_url>

'reviewbot' starts an instance of the 'celery' command using Review
Bot's 'app'. For more information please see documentation
on [Celery Application's](http://docs.celeryproject.org/en/latest/userguide/application.html)
and [Workers](http://docs.celeryproject.org/en/latest/userguide/workers.html).

