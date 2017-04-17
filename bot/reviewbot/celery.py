from __future__ import absolute_import, unicode_literals

import logging
import pkg_resources

from celery import Celery
from kombu import Exchange, Queue

from reviewbot.config import init as init_config
from reviewbot.repositories import repositories, init_repositories


celery = None


def create_queues():
    """Create the celery queues.

    Returns:
        list of kombu.Queue:
        The queues that this worker will listen to.
    """
    default_exchange = Exchange('celery', type='direct')
    queues = [
        Queue('celery', default_exchange, routing_key='celery'),
    ]

    # Detect the installed tools and select the corresponding
    # queues to consume from.
    for ep in pkg_resources.iter_entry_points(group='reviewbot.tools'):
        tool_class = ep.load()
        tool = tool_class()
        queue_name = '%s.%s' % (ep.name, tool_class.version)

        if tool.check_dependencies():
            if tool.working_directory_required:
                # Set up a queue for each configured repository. This way only
                # workers which have the relevant repository configured will
                # pick up applicable tasks.
                for repo_name in repositories:
                    repo_queue_name = '%s.%s' % (queue_name, repo_name)

                    queues.append(Queue(
                        repo_queue_name,
                        Exchange(repo_queue_name, type='direct'),
                        routing_key=repo_queue_name))
            else:
                queues.append(Queue(
                    queue_name,
                    Exchange(queue_name, type='direct'),
                    routing_key=queue_name))
        else:
            logging.warning('%s dependency check failed.', ep.name)

    return queues


def main():
    global celery

    init_config()
    init_repositories()
    celery = Celery('reviewbot.celery', include=['reviewbot.tasks'])
    celery.conf.CELERY_ACCEPT_CONTENT = ['json']
    celery.conf.CELERY_QUEUES = create_queues()
    celery.start()


if __name__ == '__main__':
    main()
