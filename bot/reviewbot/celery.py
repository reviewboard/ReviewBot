from __future__ import absolute_import

import logging
import pkg_resources

from celery import Celery
from kombu import Exchange, Queue


celery = Celery('reviewbot.celery', include=['reviewbot.tasks'])
default_exchange = Exchange('celery', type='direct')
celery.conf.CELERY_QUEUES = [
    Queue('celery', default_exchange, routing_key='celery'),
]
# Detect the installed tools and select the corresponding
# queues to consume from.
for ep in pkg_resources.iter_entry_points(group='reviewbot.tools'):
    tool_class = ep.load()
    tool = tool_class()
    qname = '%s.%s' % (ep.name, tool_class.version)

    if tool.check_dependencies():
        celery.conf.CELERY_QUEUES.append(
            Queue(qname, Exchange(qname, type='direct'), routing_key=qname))
    else:
        logging.warning("%s dependency check failed." % ep.name)


def main():
    celery.start()

if __name__ == '__main__':
    main()
