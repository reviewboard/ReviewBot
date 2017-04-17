from __future__ import unicode_literals

import json
import logging

from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from djblets.extensions.hooks import SignalHook
from reviewboard.admin.server import get_server_url
from reviewboard.integrations import Integration
from reviewboard.reviews.models import StatusUpdate
from reviewboard.reviews.signals import review_request_published

from reviewbotext.forms import ReviewBotConfigForm
from reviewbotext.models import Tool


class ReviewBotIntegration(Integration):
    """The integration for Review Bot.

    Each integration configuration corresponds to a tool that will be run when
    some conditions match.
    """

    name = 'Review Bot'
    description = _('Performs automated analysis and review on code changes.')
    config_form_cls = ReviewBotConfigForm

    def initialize(self):
        """Initialize the integration hooks."""
        SignalHook(self, review_request_published,
                   self._on_review_request_published)

    @cached_property
    def icon_static_urls(self):
        """The icons used for the integration."""
        from reviewbotext.extension import ReviewBotExtension

        extension = ReviewBotExtension.instance

        return {
            '1x': extension.get_static_url('images/reviewbot.png'),
            '2x': extension.get_static_url('images/reviewbot@2x.png'),
        }

    def _on_review_request_published(self, sender, review_request, **kwargs):
        """Handle when a review request is published.

        Args:
            sender (object):
                The sender of the signal.

            review_request (reviewboard.reviews.models.ReviewRequest):
                The review request which was published.

            **kwargs (dict):
                Additional keyword arguments.
        """
        review_request_id = review_request.get_display_id()
        diffset = review_request.get_latest_diffset()

        if not diffset:
            return

        # If this was an update to a review request, make sure that there was a
        # diff update in it. Otherwise, Review Bot doesn't care, since Review
        # Bot only deals with diffs.
        changedesc = kwargs.get('changedesc')

        if changedesc is not None:
            fields_changed = changedesc.fields_changed

            if ('diff' not in fields_changed or
                'added' not in fields_changed['diff']):
                return

        from reviewbotext.extension import ReviewBotExtension
        extension = ReviewBotExtension.instance

        matching_configs = [
            config
            for config in self.get_configs(review_request.local_site)
            if config.match_conditions(form_cls=self.config_form_cls,
                                       review_request=review_request)
        ]

        if not matching_configs:
            return

        server_url = get_server_url(local_site=review_request.local_site)

        # TODO: This creates a new session entry. We should figure out a better
        # way for Review Bot workers to authenticate to the server.
        session = extension.login_user()
        user = extension.user

        for config in matching_configs:
            tool_id = config.settings.get('tool')

            try:
                tool = Tool.objects.get(pk=tool_id)
            except Tool.DoesNotExist:
                logging.error('Skipping Review Bot integration config %s (%d) '
                              'because Tool with pk=%d does not exist.',
                              config.name, config.pk, tool_id)

            review_settings = {
                'max_comments': config.settings.get(
                    'max_comments',
                    ReviewBotConfigForm.MAX_COMMENTS_DEFAULT),
                'comment_unmodified': config.settings.get(
                    'comment_on_unmodified_code',
                    ReviewBotConfigForm.COMMENT_ON_UNMODIFIED_CODE_DEFAULT),
                'open_issues': config.settings.get(
                    'open_issues',
                    ReviewBotConfigForm.OPEN_ISSUES_DEFAULT),
            }

            try:
                tool_options = json.loads(
                    config.settings.get('tool_options', '{}'))
            except Exception as e:
                logging.exception('Failed to parse tool_options for Review '
                                  'Bot integration config %s (%d): %s',
                                  config.name, config.pk, e)
                tool_options = {}

            status_update = StatusUpdate.objects.create(
                service_id='reviewbot.%s' % tool.name,
                summary=tool.name,
                description='starting...',
                review_request=review_request,
                change_description=changedesc,
                state=StatusUpdate.PENDING,
                timeout=tool.timeout,
                user=user)

            repository = review_request.repository
            queue = '%s.%s' % (tool.entry_point, tool.version)

            if tool.working_directory_required:
                queue = '%s.%s' % (queue, repository.name)

            extension.celery.send_task(
                'reviewbot.tasks.RunTool',
                kwargs={
                    'server_url': server_url,
                    'session': session,
                    'username': user.username,
                    'review_request_id': review_request_id,
                    'diff_revision': diffset.revision,
                    'status_update_id': status_update.pk,
                    'review_settings': review_settings,
                    'tool_options': tool_options,
                    'repository_name': repository.name,
                    'base_commit_id': diffset.base_commit_id,
                },
                queue=queue)
