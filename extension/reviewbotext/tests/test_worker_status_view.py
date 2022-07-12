"""Unit tests for reviewbotext.views.WorkerStatusView."""

from __future__ import unicode_literals

import json
from collections import OrderedDict

import kgb

try:
    # Django >= 1.11, Review Board >= 4.0
    from django.urls import reverse
except ImportError:
    # Django 1.6, Review Board 3.0
    from django.core.urlresolvers import reverse

from reviewbotext.tests.testcase import TestCase


class WorkerStatusViewTests(kgb.SpyAgency, TestCase):
    """Unit tests for reviewbotext.views.WorkerStatusView."""

    def test_get(self):
        """Testing WorkerStatusView.get"""
        user = self.create_user()

        extension = self.extension
        extension.settings['user'] = user.pk
        extension.settings['broker_url'] = 'example.com'

        hosts = OrderedDict()
        hosts['user@bot1.example.com'] = {
            'status': 'ok',
            'tools': [
                {
                    'name': 'tool1',
                    'entry_point': 'path.to.tool1:Tool1',
                    'version': '1.0',
                    'description': 'Test tool 1',
                    'tool_options': [
                        {
                            'name': 'option1',
                            'field_type': ('django.forms.'
                                           'BooleanField'),
                            'default': True,
                            'field_options': {
                                'label': 'Option 1',
                                'required': False,
                                'help_text': 'Test.',
                            },
                        },
                    ],
                    'timeout': 100,
                    'working_directory_required': False,
                },
            ],
        }
        hosts['user@bot2.example.com'] = {
            'status': 'ok',
            'tools': [],
        }

        self.spy_on(self.extension.celery.control.broadcast,
                    op=kgb.SpyOpReturn([hosts]))

        response = self.client.get(reverse('reviewbot-worker-status'))

        self.assertEqual(
            json.loads(response.content.decode('utf-8')),
            {
                'state': 'success',
                'hosts': [
                    {
                        'hostname': 'bot1.example.com',
                        'tools': [
                            {
                                'name': 'tool1',
                                'entry_point': 'path.to.tool1:Tool1',
                                'version': '1.0',
                                'description': 'Test tool 1',
                                'tool_options': [
                                    {
                                        'name': 'option1',
                                        'field_type': ('django.forms.'
                                                       'BooleanField'),
                                        'default': True,
                                        'field_options': {
                                            'label': 'Option 1',
                                            'required': False,
                                            'help_text': 'Test.',
                                        },
                                    },
                                ],
                                'timeout': 100,
                                'working_directory_required': False,
                            },
                        ],
                    },
                    {
                        'hostname': 'bot2.example.com',
                        'tools': [],
                    },
                ],
            })

    def test_get_with_worker_status_error(self):
        """Testing WorkerStatusView.get with worker status=error"""
        user = self.create_user()

        extension = self.extension
        extension.settings['user'] = user.pk
        extension.settings['broker_url'] = 'example.com'

        hosts = OrderedDict()
        hosts['user@bot1.example.com'] = {
            'status': 'ok',
            'tools': [
                {
                    'name': 'tool1',
                    'entry_point': 'path.to.tool1:Tool1',
                    'version': '1.0',
                    'description': 'Test tool 1',
                    'tool_options': [
                        {
                            'name': 'option1',
                            'field_type': ('django.forms.'
                                           'BooleanField'),
                            'default': True,
                            'field_options': {
                                'label': 'Option 1',
                                'required': False,
                                'help_text': 'Test.',
                            },
                        },
                    ],
                    'timeout': 100,
                    'working_directory_required': False,
                },
            ],
        }
        hosts['user@bot2.example.com'] = {
            'status': 'error',
            'error': 'Oh no.',
        }

        self.spy_on(self.extension.celery.control.broadcast,
                    op=kgb.SpyOpReturn([hosts]))

        response = self.client.get(reverse('reviewbot-worker-status'))

        self.assertEqual(
            json.loads(response.content.decode('utf-8')),
            {
                'state': 'error',
                'error': 'Error from user@bot2.example.com: Oh no.',
            })

    def test_get_with_worker_status_unknown(self):
        """Testing WorkerStatusView.get with worker status unknown"""
        user = self.create_user()

        extension = self.extension
        extension.settings['user'] = user.pk
        extension.settings['broker_url'] = 'example.com'

        hosts = OrderedDict()
        hosts['user@bot1.example.com'] = {
            'status': 'ok',
            'tools': [
                {
                    'name': 'tool1',
                    'entry_point': 'path.to.tool1:Tool1',
                    'version': '1.0',
                    'description': 'Test tool 1',
                    'tool_options': [
                        {
                            'name': 'option1',
                            'field_type': ('django.forms.'
                                           'BooleanField'),
                            'default': True,
                            'field_options': {
                                'label': 'Option 1',
                                'required': False,
                                'help_text': 'Test.',
                            },
                        },
                    ],
                    'timeout': 100,
                    'working_directory_required': False,
                },
            ],
        }
        hosts['user@bot2.example.com'] = {}

        self.spy_on(self.extension.celery.control.broadcast,
                    op=kgb.SpyOpReturn([hosts]))

        response = self.client.get(reverse('reviewbot-worker-status'))

        self.assertEqual(
            json.loads(response.content.decode('utf-8')),
            {
                'state': 'error',
                'error': (
                    "Unexpected result when querying worker status for "
                    "user@bot2.example.com. Please check the worker's "
                    "logs for information."
                ),
            })

    def test_get_with_ioerror(self):
        """Testing WorkerStatusView.get with IOError querying workers"""
        user = self.create_user()

        extension = self.extension
        extension.settings['user'] = user.pk
        extension.settings['broker_url'] = 'example.com'

        self.spy_on(self.extension.celery.control.broadcast,
                    op=kgb.SpyOpRaise(IOError('Oh no.')))

        response = self.client.get(reverse('reviewbot-worker-status'))

        self.assertEqual(
            json.loads(response.content.decode('utf-8')),
            {
                'state': 'error',
                'error': 'Unable to connect to broker: Oh no.',
            })

    def test_get_with_not_configured(self):
        """Testing WorkerStatusView.get with Review Bot not configured"""
        self.spy_on(self.extension.celery.control.broadcast,
                    op=kgb.SpyOpReturn([]))

        response = self.client.get(reverse('reviewbot-worker-status'))

        self.assertEqual(
            json.loads(response.content.decode('utf-8')),
            {
                'state': 'error',
                'error': 'Review Bot is not yet configured.',
            })
