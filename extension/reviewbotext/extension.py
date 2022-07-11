from __future__ import unicode_literals

from importlib import import_module

from celery import Celery, VERSION as CELERY_VERSION
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.http import HttpRequest
from django.utils.translation import ugettext_lazy as _
from djblets.db.query import get_object_or_none
from reviewboard.accounts.backends import auth_backends
from reviewboard.admin.server import get_server_url
from reviewboard.extensions.base import Extension
from reviewboard.extensions.hooks import IntegrationHook

from reviewbotext.integration import ReviewBotIntegration
from reviewbotext.resources import (review_bot_review_resource,
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
    ]

    default_settings = {
        'broker_url': '',
        'user': None,
    }

    css_bundles = {
        'extension-config': {
            'source_filenames': ['css/extension-config.less'],
            'apply_to': ['reviewbot-configure'],
        },
        'integration-config': {
            'source_filenames': ['css/integration-config.less'],
        },
    }

    js_bundles = {
        'extension-config': {
            'source_filenames': [
                'js/extensionConfig.es6.js',
            ],
            'apply_to': ['reviewbot-configure'],
        },
        'integration-config': {
            'source_filenames': ['js/integrationConfig.es6.js'],
        },
    }

    @property
    def user(self):
        """The configured user."""
        return get_object_or_none(User, pk=self.settings.get('user'))

    @property
    def celery(self):
        """The celery instance."""
        stored_broker_url = self.settings['broker_url']

        if self._celery is not None and self._broker_url == stored_broker_url:
            return self._celery

        # Either we're creating the instance for the first, or the broker
        # URL has changed. Either way, we need a new instance.
        celery = Celery('reviewbot.tasks')

        if CELERY_VERSION >= (4, 0):
            celery.conf.broker_url = stored_broker_url
            celery.conf.task_serializer = 'json'
        else:
            celery.conf.BROKER_URL = stored_broker_url
            celery.conf.CELERY_TASK_SERIALIZER = 'json'

        self._broker_url = stored_broker_url
        self._celery = celery

        return celery

    @property
    def is_configured(self):
        """Whether the extension has been properly configured."""
        return self.settings['user'] and self.settings['broker_url']

    def initialize(self):
        """Initialize the extension."""
        IntegrationHook(self, ReviewBotIntegration)

        self._celery = None
        self._broker_url = None

    def login_user(self):
        """Log in as the configured user.

        This does not depend on the auth backend (hopefully). This is based on
        Client.login() with a small hack that does not require the call to
        authenticate().

        Returns:
            unicode:
            The session key of the new user session.
        """
        user = self.user

        # Review Board 3.0.8 moved all the auth backends into their own
        # modules. While the old path works for importing, it won't work
        # here because this is used to index into a dict of loaded backends
        # within the django auth middleware. 3.0.8 also shipped with a bug in
        # get_auth_backend(), so we have to use get() instead.
        backend_cls = auth_backends.get('backend_id', 'builtin')
        user.backend = '%s.%s' % (backend_cls.__module__, backend_cls.__name__)

        engine = import_module(settings.SESSION_ENGINE)

        # Create a fake request to store login details.
        request = HttpRequest()
        request.session = engine.SessionStore()
        login(request, user)
        request.session.save()
        return request.session.session_key

    def send_refresh_tools(self):
        """Request workers to update tool list."""
        payload = {
            'session': self.login_user(),
            'url': get_server_url(),
        }
        self.celery.control.broadcast('update_tools_list', payload=payload)
