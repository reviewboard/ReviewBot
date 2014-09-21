import logging
import re

from djblets.extensions.hooks import SignalHook
from reviewboard.reviews.signals import review_request_published

from reviewbotext.models import AutomaticRunGroup, ToolExecution


class SignalHandlers(object):
    """Signal handlers for Review Board signals."""

    def __init__(self, extension):
        """Initialize and connect all the signals."""
        self.extension = extension

        SignalHook(extension,
                   review_request_published,
                   self._review_request_published)

    def _review_request_published(self, **kwargs):
        """Handler for the 'review request published' signal.

        Uses AutomaticRunGroups to determine if any tool profiles should be
        automatically executed for the published review request.
        """
        # Check for a diff.
        review_request = kwargs.get('review_request')
        diffset = review_request.get_latest_diffset()

        if not diffset:
            return

        # Get the changes from the change description. The change description
        # is None only when this is a new review request (and not an update).
        changedesc = kwargs.get('changedesc')

        if changedesc is not None:
            fields_changed = changedesc.fields_changed

            # Review Bot only reviews diffs currently, so if a diff was not
            # added to the updated review request, we are done.
            if ('diff' not in fields_changed or
                'added' not in fields_changed['diff']):
                return

        review_request_id = review_request.get_display_id()
        diff_revision = diffset.revision

        profiles = set()
        files = diffset.files.all()
        auto_run_groups = AutomaticRunGroup.objects.for_repository(
            review_request.repository,
            review_request.local_site)

        for auto_run_group in auto_run_groups:
            try:
                regex = re.compile(auto_run_group.file_regex)
            except Exception, e:
                logging.error('The regex %s for AutomaticRunGroup %s could '
                              'not be compiled: %s', auto_run_group.file_regex,
                              auto_run_group.name, e)
                continue

            # If any file in the diff matches the file regex, store all tool
            # profiles in the automatic run group for execution later.
            for filediff in files:
                if (regex.match(filediff.source_file) or
                    regex.match(filediff.dest_file)):

                    for profile in auto_run_group.profile.all():
                        profiles.add(profile)

                    break

        # If the profile isn't already a queued/running/succeeded tool
        # execution, create it and add the tool execution request to the
        # message queue.
        for profile in profiles:
            execution_exists = ToolExecution.objects.filter(
                status__in=(ToolExecution.QUEUED,
                            ToolExecution.RUNNING,
                            ToolExecution.SUCCEEDED),
                profile=profile,
                review_request_id=review_request_id,
                diff_revision=diff_revision).exists()

            if not execution_exists:
                tool_execution = ToolExecution.objects.create(
                    profile=profile,
                    review_request_id=review_request_id,
                    diff_revision=diff_revision,
                    status=ToolExecution.QUEUED)
                tool_execution.save()

                request_payload = {
                    'tool_execution_id': tool_execution.id,
                    'tool_profile_id': profile.id,
                    'review_request_id': review_request_id,
                    'diff_revision': diff_revision,
                }

                self.extension.notify(request_payload)
