from __future__ import unicode_literals

from celery import Celery
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.http import HttpRequest
from django.utils.importlib import import_module
from django.utils.translation import ugettext_lazy as _
from djblets.webapi.resources import (register_resource_for_model,
                                      unregister_resource_for_model)
from reviewboard.admin.server import get_server_url
from reviewboard.extensions.base import Extension

from reviewbotext.handlers import SignalHandlers
from reviewbotext.models import ToolExecution
from reviewbotext.resources import (review_bot_review_resource,
                                    tool_executable_resource,
                                    tool_execution_resource,
                                    tool_resource)


class ReviewBotExtension(Extension):
    """An extension for communicating with Review Bot."""

    metadata = {
        'Name': 'Review Bot',
        'Summary': _('Performs automated analysis and review on code posted '
                     'to Review Board.'),
        'Author': 'Review Board',
        'Author-URL': 'http://www.reviewboard.org/',
    }

    is_configurable = True
    has_admin_site = True

    resources = [
        review_bot_review_resource,
        tool_resource,
        tool_execution_resource,
        tool_executable_resource,
    ]

    default_settings = {
        'ship_it': False,
        'comment_unmodified': False,
        'open_issues': False,
        'BROKER_URL': '',
        'user': None,
        'max_comments': 30,
    }

    def initialize(self):
        """Initialize the extension."""
        register_resource_for_model(ToolExecution, tool_execution_resource)
        self.celery = Celery('reviewbot.tasks')
        SignalHandlers(self)

    def shutdown(self, *args, **kwargs):
        """Shut down the extension."""
        unregister_resource_for_model(ToolExecution)
        super(ReviewBotExtension, self).shutdown()

    def notify(self, tool_execution_id, profile, review_request_id,
               diff_revision):
        """Initiate a review by placing a message on the message queue.

        Args:
            tool_execution_id (int):
                The pk of the ToolExecution model.

            profile (reviewbotext.models.Profile):
                The tool profile.

            review_request_id (int):
                The pk of the ReviewRequest being reviewed.

            diff_revision (int):
                The diff revision being reviewed.
        """
        self.celery.conf.BROKER_URL = self.settings['BROKER_URL']

        # TODO: this should add the local site prefix to the URL, if
        # appropriate.
        server_url = get_server_url()
        session = self._login_user(self.settings['user'])
        review_settings = {
            'comment_unmodified': profile.comment_unmodified,
            'max_comments': self.settings['max_comments'],
            'open_issues': profile.open_issues,
            'ship_it': profile.ship_it,
        }

        self.celery.send_task(
            'reviewbot.tasks.ProcessReviewRequest',
            [server_url, session, review_request_id, diff_revision,
             tool_execution_id, review_settings, profile.tool_settings],
            queue='%s.%s' % (profile.tool.entry_point,
                             profile.tool.version))

    def _login_user(self, user_id):
        """Log in as the specified user.

        This does not depend on the auth backend (hopefully). This is based on
        Client.login() with a small hack that does not require the call to
        authenticate().

        Args:
            user_id (int):
                The ID of the user to log in as.

        Returns:
            unicode:
            The key of the new user session.
        """
        user = User.objects.get(pk=user_id)
        user.backend = 'reviewboard.accounts.backends.StandardAuthBackend'
        engine = import_module(settings.SESSION_ENGINE)

        # Create a fake request to store login details.
        request = HttpRequest()
        request.session = engine.SessionStore()
        login(request, user)
        request.session.save()
        return request.session.session_key

    def send_refresh_tools(self):
        """Request workers to update tool list."""
        self.celery.conf.BROKER_URL = self.settings['BROKER_URL']
        payload = {
            'session': self._login_user(self.settings['user']),
            'url': get_server_url(),
        }
        self.celery.control.broadcast('update_tools_list', payload=payload)
