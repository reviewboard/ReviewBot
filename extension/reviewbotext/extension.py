import os

from celery.execute import send_task
from reviewboard.extensions.base import Extension

from reviewbotext.handlers import SignalHandlers


class ReviewBotExtension(Extension):
    """An extension for communicating with Review Bot"""
    is_configurable = True
    default_settings = {
        'ship_it': False,
        'BROKER_URL': '',
        'user': '',
        'password': '',
    }

    def __init__(self, *args, **kwargs):
        super(ReviewBotExtension, self).__init__()
        self.settings.load()
        self.signal_handlers = SignalHandlers(self)

    def notify(self, request_payload):
        """
        Add the request to the queue
        """

        # Set up the Celery configuration.
        temp = ''
        if 'CELERY_CONFIG_MODULE' in os.environ:
            temp = os.environ['CELERY_CONFIG_MODULE']
        os.environ['CELERY_CONFIG_MODULE'] = 'reviewbotext.celeryconfig'

        # Add the request to the queue.
        payload = {
            'user': self.settings['user'],
            'password': self.settings['password'],
            'ship_it': self.settings['ship_it'],
            'request': request_payload,
        }

        try:
            send_task("reviewbot.processing.tasks.ProcessReviewRequest",
                      [payload])
        except:
            raise

        # Restore the previous Celery configuration.
        os.environ['CELERY_CONFIG_MODULE'] = temp
