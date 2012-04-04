import os

from celery.execute import send_task
from reviewboard.extensions.base import Extension

from reviewbotext.handlers import SignalHandlers


class ReviewBotExtension(Extension):
    """An extension for communicating with Review Bot"""
    is_configurable = True
    default_settings = {
        'ship_it': False,
        'comment_unmodified': False,
        'open_issues': False,
        'BROKER_URL': '',
        'rb_url': '',
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
        review_settings = {
            'ship_it': self.settings['ship_it'],
            'comment_unmodified': self.settings['comment_unmodified'],
            'open_issues': self.settings['open_issues'],
        }
        payload = {
            'user': self.settings['user'],
            'password': self.settings['password'],
            'url': self.settings['rb_url'],
            'ship_it': self.settings['ship_it'],
            'request': request_payload,
            'settings': review_settings,
        }

        try:
            send_task("reviewbot.tasks.ProcessReviewRequest",
                      [payload])
        except:
            raise

        # Restore the previous Celery configuration.
        os.environ['CELERY_CONFIG_MODULE'] = temp
