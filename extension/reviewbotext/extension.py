import os

from celery import Celery
from reviewboard.extensions.base import Extension

from reviewbotext.handlers import SignalHandlers
from reviewbotext.resources import review_bot_review_resource


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
    resources = [review_bot_review_resource]

    def __init__(self, *args, **kwargs):
        super(ReviewBotExtension, self).__init__()
        self.settings.load()
        self.celery = Celery('reviewbot.tasks')
        self.signal_handlers = SignalHandlers(self)

    def notify(self, request_payload):
        """
        Add the request to the queue
        """
        self.celery.conf.BROKER_URL = self.settings['BROKER_URL']

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
            self.celery.send_task("reviewbot.tasks.ProcessReviewRequest",
                                  [payload])
        except:
            raise
