from __future__ import absolute_import, unicode_literals

import logging

from celery import Celery, VERSION as CELERY_VERSION
from celery.signals import celeryd_after_setup
from kombu import Exchange, Queue

from reviewbot.config import load_config
from reviewbot.repositories import repositories, init_repositories
from reviewbot.tools.base.registry import (get_tool_classes,
                                           load_tool_classes)


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

    # Detect the installed tools and select the corresponding queues to
    # consume from.
    for tool_class in get_tool_classes():
        tool_id = tool_class.tool_id
        tool = tool_class()
        queue_name = '%s.%s' % (tool_id, tool_class.version)

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
            logging.warning('%s dependency check failed.', tool_id)

    return queues


@celeryd_after_setup.connect
def setup_reviewbot(instance, conf, **kwargs):
    """Set up Review Bot and Celery.

    This will load the Review Bot configuration, store any repository state,
    and set up the queues for the enabled tools.

    Args:
        instance (celery.app.base.Celery):
            The Celery instance.

        conf (celery.app.utils.Settings):
            The Celery configuration.

        **kwargs (dict, unused):
            Additional keyword arguments passed to the signal.
    """
    load_config()
    load_tool_classes()
    init_repositories()

    if CELERY_VERSION >= (4, 0):
        conf.accept_content = ['json']
    else:
        conf.CELERY_ACCEPT_CONTENT = ['json']

    instance.app.amqp.queues = create_queues()


def main():
    global celery

    celery = Celery('reviewbot.celery', include=['reviewbot.tasks'])
    celery.start()


if __name__ == '__main__':
    main()
