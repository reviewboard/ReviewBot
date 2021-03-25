from __future__ import absolute_import, unicode_literals

import logging
import os
import sys

from celery import Celery, VERSION as CELERY_VERSION
from celery.signals import celeryd_after_setup
from kombu import Exchange, Queue

from reviewbot.config import config, load_config
from reviewbot.repositories import repositories, init_repositories
from reviewbot.tools.base.registry import (get_tool_classes,
                                           load_tool_classes)


celery = Celery('reviewbot.celery', include=['reviewbot.tasks'])


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


def setup_cookies():
    """Set up cookie storage for API communication.

    This will ensure that the cookie directory exists and that the cookie
    file can be written to.

    Raises:
        IOError:
            The cookie directories could not be created or there's a
            permission error with cookie storage. The specific error will
            be in the exception message.
    """
    cookie_dir = config['cookie_dir']
    cookie_path = config['cookie_path']

    logging.debug('Checking cookie storage at %s', cookie_path)

    # Create the cookie storage directory, if it doesn't exist.
    if not os.path.exists(cookie_dir):
        try:
            os.makedirs(cookie_dir, 0o755)
        except OSError as e:
            raise IOError('Unable to create cookies directory "%s": %s'
                          % (cookie_dir, e))

    can_write_cookies = True

    if os.path.exists(cookie_path):
        # See if we have write access to the file.
        can_write_cookies = os.access(cookie_path, os.W_OK)
    else:
        # Try writing to the file. We'll append, just in case there's another
        # process that managed to write just before this (super unlikely).
        try:
            with open(cookie_path, 'a'):
                pass

            os.chmod(cookie_path, 0o600)
        except (IOError, OSError):
            can_write_cookies = False

    if not can_write_cookies:
        raise IOError('Unable to write to cookie file "%s". Please make '
                      'sure Review Bot has the proper permissions.'
                      % cookie_path)

    logging.debug('Cookies can be stored at %s', cookie_path)


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

    try:
        setup_cookies()
    except IOError as e:
        logging.error(e)
        sys.exit(1)

    load_tool_classes()
    init_repositories()

    if CELERY_VERSION >= (4, 0):
        conf.accept_content = ['json']
    else:
        conf.CELERY_ACCEPT_CONTENT = ['json']

    instance.app.amqp.queues = create_queues()


def main():
    celery.start()


if __name__ == '__main__':
    main()
