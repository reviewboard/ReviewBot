from __future__ import absolute_import

import pkg_resources

from celery import Celery
from celery.worker.control import Panel
from kombu import Exchange, Queue


celery = Celery('reviewbot.celery', include=['reviewbot.tasks'])


default_exchange = Exchange('celery', type='direct')
celery.conf.CELERY_QUEUES = [
    Queue('celery', default_exchange, routing_key='celery'),
]
# Detect the installed tools and select the corresponding
# queues to consume from.
for ep in pkg_resources.iter_entry_points(group='reviewbot.tools'):
    tool = ep.load()
    qname = '%s.%s' % (ep.name, tool.version)
    celery.conf.CELERY_QUEUES.append(
        Queue(qname, Exchange(qname, type='direct'), routing_key=qname))


@Panel.register
def update_tools_list(panel):
    pass
    return {'ok': 'Tool list update complete.'}

if __name__ == '__main__':
    celery.start()
