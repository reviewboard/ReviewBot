from celery import Celery
from reviewboard.extensions.base import Extension

from reviewbotext.handlers import SignalHandlers
from reviewbotext.models import ReviewBotTool
from reviewbotext.resources import review_bot_review_resource, \
                                   review_bot_tool_resource


class ReviewBotExtension(Extension):
    """An extension for communicating with Review Bot"""
    is_configurable = True
    has_admin_site = True
    default_settings = {
        'ship_it': False,
        'comment_unmodified': False,
        'open_issues': False,
        'BROKER_URL': '',
        'rb_url': '',
        'user': '',
        'password': '',
    }
    resources = [
        review_bot_review_resource,
        review_bot_tool_resource,
    ]

    def __init__(self, *args, **kwargs):
        super(ReviewBotExtension, self).__init__()
        self.settings.load()
        self.celery = Celery('reviewbot.tasks')
        self.signal_handlers = SignalHandlers(self)

    def shutdown(self):
        self.signal_handlers.disconnect()
        super(ReviewBotExtension, self).shutdown()

    def notify(self, request_payload):
        """Add the request to the queue."""
        self.celery.conf.BROKER_URL = self.settings['BROKER_URL']

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
        tools = ReviewBotTool.objects.filter(enabled=True,
                                             run_automatically=True)
        for tool in tools:
            try:
                self.celery.send_task(
                    "reviewbot.tasks.ProcessReviewRequest",
                    [payload, tool.tool_settings],
                    queue='%s.%s' % (tool.entry_point, tool.version))
            except:
                raise

    def send_refresh_tools(self):
        """Request workers to update tool list."""
        self.celery.conf.BROKER_URL = self.settings['BROKER_URL']
        payload = {
            'user': self.settings['user'],
            'password': self.settings['password'],
            'url': self.settings['rb_url'],
        }
        self.celery.control.broadcast('update_tools_list', payload=payload)
