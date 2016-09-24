from __future__ import absolute_import, unicode_literals

import logging
import pkg_resources

from celery import Celery
from kombu import Exchange, Queue


default_exchange = Exchange('celery', type='direct')
celery = Celery('reviewbot.celery', include=['reviewbot.tasks'])
celery.conf.CELERY_QUEUES = [
    Queue('celery', default_exchange, routing_key='celery'),
]


# Detect the installed tools and select the corresponding
# queues to consume from.
for ep in pkg_resources.iter_entry_points(group='reviewbot.tools'):
    tool_class = ep.load()
    tool = tool_class()
    queue_name = '%s.%s' % (ep.name, tool_class.version)

    if tool.check_dependencies():
        celery.conf.CELERY_QUEUES.append(
            Queue(queue_name, Exchange(queue_name, type='direct'),
                  routing_key=queue_name))
    else:
        logging.warning('%s dependency check failed.', ep.name)


def main():
    celery.start()


if __name__ == '__main__':
    main()
