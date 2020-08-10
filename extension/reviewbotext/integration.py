from __future__ import unicode_literals

import json
import logging
from datetime import datetime

from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from djblets.extensions.hooks import SignalHook
from reviewboard.admin.server import get_server_url
from reviewboard.diffviewer.models import DiffSet
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

        try:
            from reviewboard.reviews.signals import status_update_request_run
            SignalHook(self, status_update_request_run,
                       self._on_status_update_request_run)
        except ImportError:
            # Running on Review Board 3.0.18 or older.
            pass

    @cached_property
    def icon_static_urls(self):
        """The icons used for the integration."""
        from reviewbotext.extension import ReviewBotExtension

        extension = ReviewBotExtension.instance

        return {
            '1x': extension.get_static_url('images/reviewbot.png'),
            '2x': extension.get_static_url('images/reviewbot@2x.png'),
        }

    def _get_matching_configs(self, review_request, service_id=None):
        """Return the matching configurations for a review request.

        Args:
            review_request (reviewboard.reviews.models.ReviewRequest):
                The review request to get Review Bot configurations for.

            service_id (unicode, optional):
                A service ID to filter for.

        Yields:
            tuple:
            A 4-tuple of the following:

            * The config instance.
            * The tool model to use (:py:class:`reviewbotext.models.Tool`)
            * The tool options (:py:class:`dict`). This contains the matching
              configuration's settings specific to the tool.
            * The review settings (:py:class:`dict`). This contains settings
              common to all integration configurations.

            The tool options dictionary contains the matching configuration's
            settings specific to the tool.
        """
        matching_configs = [
            config
            for config in self.get_configs(review_request.local_site)
            if config.match_conditions(form_cls=self.config_form_cls,
                                       review_request=review_request)
        ]

        for config in matching_configs:
            if (service_id is not None and
                'reviewbot.%s' % config.id != service_id):
                continue

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
                'run_manually': config.settings.get(
                    'run_manually',
                    ReviewBotConfigForm.RUN_MANUALLY_DEFAULT),
            }

            try:
                tool_options = json.loads(
                    config.settings.get('tool_options', '{}'))
            except Exception as e:
                logging.exception('Failed to parse tool_options for Review '
                                  'Bot integration config %s (%d): %s',
                                  config.name, config.pk, e)
                tool_options = {}

            yield config, tool, tool_options, review_settings

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

        matching_configs = self._get_matching_configs(review_request)

        if not matching_configs:
            return

        server_url = get_server_url(local_site=review_request.local_site)

        # TODO: This creates a new session entry. We should figure out a better
        # way for Review Bot workers to authenticate to the server.
        session = extension.login_user()
        user = extension.user

        for config, tool, tool_options, review_settings in matching_configs:
            # Use the config ID rather than the tool name because it is unique
            # and unchanging. This allows us to find other status updates from
            # the same tool config.
            service_id = 'reviewbot.%s' % config.id

            if config.settings.get('drop_old_issues'):
                self._drop_old_issues(user, service_id, review_request)

            status_update = StatusUpdate(
                service_id=service_id,
                summary=tool.name,
                review_request=review_request,
                change_description=changedesc,
                state=StatusUpdate.PENDING,
                timeout=tool.timeout,
                user=user)
            status_update.extra_data['can_retry'] = True

            if review_settings['run_manually']:
                status_update.description = 'waiting to run.'
                status_update.state = StatusUpdate.NOT_YET_RUN
                status_update.save()
            else:
                status_update.save()

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

    def _drop_old_issues(self, user, service_id, review_request):
        """Drop old issues associated with the given tool config.

        Args:
            user (django.contrib.auth.models.User):
                The Review Bot user.

            service_id (unicode):
                The service ID set on the status update objects.

            review_request (reviewboard.reviews.models.ReviewRequest):
                The review request that Review Bot is currently checking.
        """
        status_updates = (
            StatusUpdate.objects.all()
            .filter(user=user,
                    service_id=service_id,
                    review_request=review_request)
            .exclude(review__isnull=True)
            .select_related('review')
        )

        for update in status_updates:
            update.drop_open_issues()

    def _on_status_update_request_run(self, sender, status_update, **kwargs):
        """Handle a request to run or rerun a tool.

        Args:
            sender (object):
                The sender of the signal

            status_update (reviewboard.reviews.models.StatusUpdate):
                The status update for the tool that should be run.

            **kwargs (dict):
                Any additional keyword arguments.
        """
        service_id = status_update.service_id

        if not service_id.startswith('reviewbot.'):
            # Ignore anything that's not Review Bot.
            return

        review_request = status_update.review_request
        matching_configs = list(self._get_matching_configs(
            review_request, service_id=service_id))

        if not matching_configs:
            # While the service ID indentified status_update as coming from
            # Review Bot, it doesn't match any active configs, so there's
            # nothing we can do.
            return

        server_url = get_server_url(local_site=review_request.local_site)

        from reviewbotext.extension import ReviewBotExtension
        extension = ReviewBotExtension.instance

        # TODO: This creates a new session entry. We should figure out a better
        # way for Review Bot workers to authenticate to the server.
        session = extension.login_user()
        user = extension.user

        assert len(matching_configs) == 1
        config, tool, tool_options, review_settings = matching_configs[0]

        status_update.description = 'starting...'
        status_update.state = StatusUpdate.PENDING
        status_update.timestamp = datetime.now()
        status_update.save(update_fields=('description', 'state', 'timestamp'))

        repository = review_request.repository
        queue = '%s.%s' % (tool.entry_point, tool.version)

        if tool.working_directory_required:
            queue = '%s.%s' % (queue, repository.name)

        changedesc = status_update.change_description

        # If there's a change description associated with the status
        # update, then use the diff from that. Otherwise, choose the first
        # diffset on the review request.
        try:
            if changedesc and 'diff' in changedesc.fields_changed:
                new_diff = changedesc.fields_changed['diff']['added'][0]
                diffset = DiffSet.objects.get(pk=new_diff[2])
            else:
                diffset = DiffSet.objects.filter(
                    history=review_request.diffset_history_id).earliest()
        except DiffSet.DoesNotExist:
            logging.error('Unable to determine diffset when running '
                          'Review Bot tool for status update %d',
                          status_update.pk)
            return

        extension.celery.send_task(
            'reviewbot.tasks.RunTool',
            kwargs={
                'server_url': server_url,
                'session': session,
                'username': user.username,
                'review_request_id': review_request.get_display_id(),
                'diff_revision': diffset.revision,
                'status_update_id': status_update.pk,
                'review_settings': review_settings,
                'tool_options': tool_options,
                'repository_name': repository.name,
                'base_commit_id': diffset.base_commit_id,
            },
            queue=queue)
