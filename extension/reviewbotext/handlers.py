from reviewboard.reviews.signals import review_request_published


class SignalHandlers(object):
    """Signal handlers for reviewboard signals."""

    def __init__(self, extension):
        """Initialize and connect all the signals"""
        self.extension = extension

        # Connect the handlers.
        review_request_published.connect(self._review_request_published)

    def disconnect(self):
        """Disconnect the signal handlers"""
        review_request_published.disconnect(self._review_request_published)

    def _review_request_published(self, **kwargs):
        review_request = kwargs.get('review_request')
        review_request_id = review_request.get_display_id()

        # Get the changes from the change description.
        changedesc = kwargs.get('changedesc')

        if changedesc is not None:
            is_new = False
            fields_changed = changedesc.fields_changed

            # Check for a diff.
            try:
                diff_revision_string = fields_changed['diff']['added'][0][0]
                diff_revision = int(diff_revision_string.lstrip('Diff r'))
                has_diff = True
            except:
                has_diff = False
        else:
            is_new = True
            fields_changed = {}

            # Check for a diff:
            diffsets = review_request.diffset_history.diffsets.get_query_set()
            if len(diffsets) > 0:
                has_diff = True
                diff_revision = diffsets[0].revision
            else:
                has_diff = False

        request_payload = {
            'review_request_id': review_request_id,
            'new': is_new,
            'fields_changed': fields_changed,
            'has_diff': has_diff,
        }

        if has_diff:
            request_payload['diff_revision'] = diff_revision
            self.extension.notify(request_payload)
