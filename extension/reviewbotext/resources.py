import json

from django.core.exceptions import ObjectDoesNotExist

from djblets.webapi.decorators import webapi_login_required, \
                                      webapi_response_errors, \
                                      webapi_request_fields
from djblets.webapi.errors import DOES_NOT_EXIST, INVALID_FORM_DATA, \
                                  NOT_LOGGED_IN, PERMISSION_DENIED

from reviewboard.diffviewer.models import FileDiff
from reviewboard.reviews.models import Comment, BaseComment, Review
from reviewboard.webapi.decorators import webapi_check_local_site
from reviewboard.webapi.resources import WebAPIResource, \
                                         review_request_resource


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
        """Creates a new review and publishes it.

        """
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

                    new_comment = new_review.comments.create(
                        filediff=filediff,
                        interfilediff=None,
                        text=comment['text'],
                        first_line=comment['first_line'],
                        num_lines=comment['num_lines'])

                    if comment['issue_opened']:
                        new_comment.issue_status = BaseComment.OPEN
                    else:
                        new_comment.issue_status = None

                    new_comment.save()
                    #new_review.comments.add(new_comment)
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
