import json

from django.core.exceptions import ObjectDoesNotExist

from djblets.webapi.decorators import webapi_login_required, \
                                      webapi_response_errors, \
                                      webapi_request_fields
from djblets.webapi.errors import DOES_NOT_EXIST, INVALID_FORM_DATA, \
                                  NOT_LOGGED_IN, PERMISSION_DENIED

from reviewboard.diffviewer.models import FileDiff
from reviewboard.extensions.base import get_extension_manager
from reviewboard.reviews.models import BaseComment, Review, ReviewRequest
from reviewboard.webapi.decorators import webapi_check_local_site
from reviewboard.webapi.resources import WebAPIResource, \
                                         review_request_resource

from reviewbotext.models import ReviewBotTool


class ReviewBotReviewResource(WebAPIResource):
    """Resource for creating reviews with a single request.

    This resource allows Review Bot to create a full review using a single
    POST request. Using the traditional API would result in a high volume
    of requests from Review Bot, creating stress on the server.

    Each user may only have one review draft per request at a time. This
    resource allows concurrent review of a single request by creating
    the review and publishing it in a single transaction.
    """
    name = 'review_bot_review'
    allowed_methods = ('GET', 'POST',)

    @webapi_check_local_site
    @webapi_login_required
    @webapi_response_errors(DOES_NOT_EXIST, INVALID_FORM_DATA,
                            NOT_LOGGED_IN, PERMISSION_DENIED)
    @webapi_request_fields(
        required={
            'review_request_id': {
                'type': int,
                'description': 'The ID of the review request.'
            },
        },
        optional={
            'ship_it': {
                'type': bool,
                'description': 'Whether or not to mark the review "Ship It!"',
            },
            'body_top': {
                'type': str,
                'description': 'The review content above the comments.',
            },
            'body_bottom': {
                'type': str,
                'description': 'The review content below the comments.',
            },
            'diff_comments': {
                'type': str,
                'description': 'A JSON payload containing the diff comments',
            },
        },
    )
    def create(self, request, review_request_id, ship_it=False, body_top='',
               body_bottom='', diff_comments=None, *args, **kwargs):
        """Creates a new review and publishes it."""
        try:
            review_request = \
                review_request_resource.get_object(request, review_request_id,
                                                   *args, **kwargs)
        except ObjectDoesNotExist:
            return DOES_NOT_EXIST

        if not body_top:
            body_top = ''

        if not body_bottom:
            body_bottom = ''

        new_review = Review.objects.create(
            review_request=review_request,
            user=request.user,
            body_top=body_top,
            body_bottom=body_bottom,
            ship_it=ship_it)

        if diff_comments:
            try:
                diff_comments = json.loads(diff_comments)
                for comment in diff_comments:
                    filediff = FileDiff.objects.get(
                        pk=comment['filediff_id'],
                        diffset__history__review_request=review_request)

                    if comment['issue_opened']:
                        issue = True
                        issue_status = BaseComment.OPEN
                    else:
                        issue = False
                        issue_status = None

                    new_review.comments.create(
                        filediff=filediff,
                        interfilediff=None,
                        text=comment['text'],
                        first_line=comment['first_line'],
                        num_lines=comment['num_lines'],
                        issue_opened=issue,
                        issue_status=issue_status)

            except KeyError:
                # TODO: Reject the DB transaction.
                return INVALID_FORM_DATA, {
                    'fields': {
                        'diff_comments': 'Diff comments were malformed',
                    },
                }
            except ObjectDoesNotExist:
                return INVALID_FORM_DATA, {
                    'fields': {
                        'diff_comments': 'Invalid filediff_id',
                    },
                }

        new_review.publish(user=request.user)

        return 201, {
            self.item_result_key: new_review,
        }

review_bot_review_resource = ReviewBotReviewResource()


class ReviewBotToolResource(WebAPIResource):
    """Resource for workers to update the installed tools list.

    Also provides information on the installed Review Bot tools. This can be
    used to fetch the list of installed tools to be displayed in the Review
    Board UI.

    """
    name = 'review_bot_tool'
    allowed_methods = ('GET', 'POST',)
    model = ReviewBotTool
    model_object_key = 'id'
    uri_object_key = 'reviewbot_tool_id'
    fields = {
        'id': {
            'type': int,
            'description': 'The id of the tool.',
        },
        'name': {
            'type': str,
            'description': 'The name of the tool.',
        },
        'version': {
            'type': str,
            'description': 'The tool version number.',
        },
        'enabled': {
            'type': bool,
            'description': 'Whether the user has enabled this '
                           'tool in the Review Bot extension.',
        },
        'run_automatically': {
            'type': bool,
            'description': 'Whether the user has enabled this tool to '
                           'run automatically.',
        },
        'allow_run_manually': {
            'type': bool,
            'description': 'Whether the user has enabled this tool to '
                           'be triggered manually.',
        },
    }

    @webapi_check_local_site
    @webapi_login_required
    @webapi_response_errors(DOES_NOT_EXIST, INVALID_FORM_DATA,
                            NOT_LOGGED_IN, PERMISSION_DENIED)
    @webapi_request_fields(
        required={
            'hostname': {
                'type': str,
                'description': 'The hostname of the POSTing worker.',
            },
            'tools': {
                'type': str,
                'description': 'A JSON payload containing tool information.',
            },
        },
    )
    def create(self, request, hostname, tools, *args, **kwargs):
        """Add to the list of installed tools.

        The hostname field should contain the hostname the celery
        worker is using (This should be unique to that worker under
        proper configuration).

        The tools file should contain a JSON payload describing the
        list of tools installed at the worker. This payload should
        correspond to a list of dictionaries, with each dictionary
        corresponding to a tool. The dictionary should contain the
        following information:
            - 'name': The descriptive name of the tool.
            - 'entry_point': The entry point corresponding to the tool.
            - 'version': The tool version.
            - 'description': Longer description of the tool.
            - 'tool_options': A JSON payload describing the custom
              options the tool provides.

        TODO: Use the hostname.
        """
        try:
            tools = json.loads(tools)
        except:
            return INVALID_FORM_DATA, {
                    'fields': {
                        'dtools': 'Malformed JSON.',
                    },
                }

        for tool in tools:
            # TODO: Defaulting the settings should maybe
            # occure when sending out payloads, not here.
            # or it could be taken care of on the tool
            # side.
            options = json.loads(str(tool['tool_options']))
            settings = {}
            for opt in options:
                settings[opt['name']] = opt.get('default', None)

            obj, created = ReviewBotTool.objects.get_or_create(
                entry_point=tool['entry_point'],
                version=tool['version'],
                defaults={
                    'name': tool['name'],
                    'description': tool['description'],
                    'tool_options': tool['tool_options'],
                    'tool_settings': json.dumps(settings),
                    'in_last_update': True,
                })
            if not created and not obj.in_last_update:
                obj.in_last_update = True
                obj.save()

        # TODO: Fix the result key here.
        return 201, {}

review_bot_tool_resource = ReviewBotToolResource()


class ReviewBotTriggerReviewResource(WebAPIResource):
    """Resource that triggers a set of ReviewBot reviews given a list of tools
    to run on a review request.

    Can be called from within the ReviewBoard UI for the purpose of manually
    triggering ReviewBot reviews.

    """
    name = 'review_bot_trigger_review'
    allowed_methods = ('POST',)

    @webapi_check_local_site
    @webapi_login_required
    @webapi_response_errors(DOES_NOT_EXIST, INVALID_FORM_DATA,
                            NOT_LOGGED_IN, PERMISSION_DENIED)
    @webapi_request_fields(
        required={
            'review_request_id': {
                'type': int,
                'description': 'ID of the review request to be reviewed.',
            },
            'tools': {
                'type': str,
                'description': 'A JSON payload containing tool information.',
            },
        },
    )
    def create(self, request, review_request_id, tools, *args, **kwargs):
        """Trigger ReviewBot review(s) based on the set of given tools.

        """
        try:
            tools = json.loads(tools)

        except:
            return INVALID_FORM_DATA, {
                'fields': {
                    'dtools': 'Malformed JSON.',
                },
            }

        # Get the ReviewBotExtension instance. We can assume it exists because
        # this code is executed after the extension has been registered with
        # the manager.
        from reviewbotext.extension import ReviewBotExtension
        extension_manager = get_extension_manager()
        extension = \
            extension_manager.get_enabled_extension(ReviewBotExtension.id)
        review_request = ReviewRequest.objects.get(id=review_request_id)
        is_new = True
        fields_changed = {}

        # Check for a diff:
        diffsets = review_request.diffset_history.diffsets.get_query_set()
        if len(diffsets) > 0:
            has_diff = True
            diff_revision = diffsets[len(diffsets)-1].revision
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

        extension.notify(request_payload, tools)

        # TODO: Fix the result key here.
        return 201, {}

review_bot_trigger_review_resource = ReviewBotTriggerReviewResource()
