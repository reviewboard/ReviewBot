"""API resources for the extension."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, overload

from django.core.exceptions import ObjectDoesNotExist
from djblets.webapi.decorators import (webapi_login_required,
                                       webapi_request_fields,
                                       webapi_response_errors)
from djblets.webapi.errors import (DOES_NOT_EXIST,
                                   INVALID_FORM_DATA,
                                   NOT_LOGGED_IN,
                                   PERMISSION_DENIED)
from reviewboard.diffviewer.models import FileDiff
from reviewboard.reviews.models import BaseComment, Review
from reviewboard.webapi.decorators import webapi_check_local_site
from reviewboard.webapi.resources import resources, WebAPIResource
from typing_extensions import NotRequired, TypedDict

from reviewbotext.models import Tool

if TYPE_CHECKING:
    from typing import Any, Literal, Mapping

    from django.http import HttpRequest
    from djblets.webapi.resources.base import WebAPIResourceHandlerResult


class GeneralCommentData(TypedDict):
    """Data for a general comment.

    Version Added:
        4.1
    """

    #: Whether the comment has an open issue.
    issue_opened: bool

    #: The issue status for the comment.
    issue_status: str | None

    #: Whether the text should be formatted using Markdown.
    rich_text: bool

    #: The comment text.
    text: str


class DiffCommentData(GeneralCommentData):
    """Data for a diff comment.

    Version Added:
        4.1
    """

    #: The filediff the comment applies to.
    #:
    #: This must be set before creating the comment.
    filediff: NotRequired[FileDiff]

    #: The ID of the file diff the comment applies to.
    #:
    #: This is used to set ``filediff`` and then removed.
    filediff_id: NotRequired[int]

    #: The first line of the comment range.
    first_line: int

    #: The interfilediff the comment applies to.
    #:
    #: This is always ``None`` since Review Bot doesn't review interdiffs.
    interfilediff: NotRequired[None]

    #: The number of lines in the comment range.
    num_lines: int


class InvalidFormDataError(Exception):
    """Error that signals to return INVALID_FORM_DATA with attached data."""

    def __init__(
        self,
        data: Mapping[str, Any],
    ) -> None:
        """Initialize the Error.

        Args:
            data (dict):
                The data that should be returned from the webapi method.
        """
        self.data = data


class ToolResource(WebAPIResource):
    """Resource for workers to update the installed tools list.

    This API endpoint isn't actually RESTful, and just provides a place
    for workers to "dump" their entire list of installed tools as a single
    POST. A GET request will not actually return a list of tools.
    """

    name = 'tool'
    allowed_methods = ('GET', 'POST')
    model_object_key = 'id'
    uri_object_key = 'tool_id'

    @webapi_login_required
    @webapi_check_local_site
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
    def create(
        self,
        request: HttpRequest,
        hostname: str,
        tools: str,
        *args,
        **kwargs,
    ) -> WebAPIResourceHandlerResult:
        """Add to the list of installed tools.

        The hostname field should contain the hostname the celery
        worker is using (This should be unique to that worker under
        proper configuration).

        The tools field should contain a JSON payload describing the
        list of tools installed at the worker. This payload should
        correspond to a list of dictionaries, with each dictionary
        corresponding to a tool. The dictionary should contain the
        following information:
            - 'name': The descriptive name of the tool.
            - 'entry_point': The entry point corresponding to the tool.
            - 'version': The tool version.
            - 'description': Longer description of the tool.
            - 'tool_options': A JSON payload describing the custom
              options the tool provides (see reviewbotext.models.Tool
              for a description of this payload).

        Here is an example tools payload:
        [
          {
            "name": "Example Tool 1",
            "entry_point": "example1",
            "version": "1.0.1",
            "description": "An example tool.",
            "tool_options": "[]"
          },
          {
            "name": "Example Tool 2",
            "entry_point": "example2",
            "version": "1.2.1",
            "description": "The second example tool.",
            "tool_options": "[]"
          },
        ]

        TODO: Use the hostname.
        """
        from reviewbotext.extension import ReviewBotExtension
        extension = ReviewBotExtension.instance

        # Ensure the request is from the Review Bot user
        if request.user.id != extension.settings['user']:
            return PERMISSION_DENIED

        try:
            tools = json.loads(tools)
        except Exception:
            return INVALID_FORM_DATA, {
                'fields': {
                    'dtools': 'Malformed JSON.',
                },
            }

        for tool in tools:
            obj, created = Tool.objects.get_or_create(
                entry_point=tool['entry_point'],
                version=tool['version'],
                defaults={
                    'name': tool['name'],
                    'description': tool['description'],
                    'tool_options': tool['tool_options'],
                    'in_last_update': True,
                    'timeout': tool['timeout'],
                    'working_directory_required':
                        tool['working_directory_required'],
                })

            if not created and not obj.in_last_update:
                obj.in_last_update = True
                obj.save()

        # TODO: Fix the result key here.
        return 201, {}


tool_resource = ToolResource()


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

    @webapi_login_required
    @webapi_check_local_site
    @webapi_response_errors(DOES_NOT_EXIST, INVALID_FORM_DATA,
                            NOT_LOGGED_IN, PERMISSION_DENIED)
    @webapi_request_fields(
        required={
            'review_request_id': {
                'type': int,
                'description': 'The ID of the review request.',
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
            'body_top_rich_text': {
                'type': bool,
                'description': 'Whether the body-top should be formatted '
                               'using Markdown.',
            },
            'body_bottom': {
                'type': str,
                'description': 'The review content below the comments.',
            },
            'body_bottom_rich_text': {
                'type': bool,
                'description': 'Whether the body-bottom should be formatted '
                               'using Markdown.',
            },
            'diff_comments': {
                'type': str,
                'description': 'A JSON payload containing the diff comments.',
            },
            'general_comments': {
                'type': str,
                'description':
                    'A JSON payload containing the general comments.',
            },
            'to_owner_only': {
                'type': bool,
                'description':
                    'When enabled, e-mail notifications will only be sent '
                    'to the owner of the review request.',
                'added_in': '4.1',
            },
        },
    )
    def create(
        self,
        request: HttpRequest,
        review_request_id: int,
        ship_it: bool = False,
        body_top: str = '',
        body_top_rich_text: bool = False,
        body_bottom: str = '',
        body_bottom_rich_text: bool = False,
        diff_comments: (str | None) = None,
        general_comments: (str | None) = None,
        *args,
        to_owner_only: bool = False,
        **kwargs,
    ) -> WebAPIResourceHandlerResult:
        """Create a new review and publishes it.

        Version Changed:
            4.1:
            Added the ``to_owner_only`` argument.

        Args:
            request (django.http.HttpRequest):
                The HTTP request.

            review_request_id (int):
                The ID of the review request being reviewed (ID for use in the
                API, which is the "display_id" field).

            ship_it (bool, optional):
                The Ship It state for the review.

            body_top (str, optional):
                The text for the ``body_top`` field.

            body_top_rich_text (bool, optional):
                Whether the body_top text should be formatted using Markdown.

            body_bottom (str, optional):
                The text for the ``body_bottom`` field.

            body_bottom_rich_text (bool, optional):
                Whether the body_bottom text should be formatted using
                Markdown.

            diff_comments (str, optional):
                A JSON payload containing the diff comments.

            general_comments (str, optional):
                A JSON payload containing the general comments.

            *args (tuple):
                Positional arguments to set in the review.

            to_owner_only (bool):
                When enabled, e-mail notifications will only be sent to the
                owner of the review request.

                Version Added:
                    4.1

            **kwargs (dict):
                Additional attributes to set in the review.

        Returns:
            tuple:
            A 2-tuple containing an HTTP return code and the API payload.
        """
        try:
            review_request = resources.review_request.get_object(
                request,
                review_request_id=review_request_id,
                *args, **kwargs)
        except ObjectDoesNotExist:
            return DOES_NOT_EXIST

        if not body_top:
            body_top = ''

        if not body_bottom:
            body_bottom = ''

        try:
            diff_comment_keys = {'filediff_id', 'first_line', 'num_lines'}
            diff_comments_norm = self._normalize_comments_json(
                'diff_comments', diff_comment_keys, diff_comments)

            general_comments_norm = self._normalize_comments_json(
                'general_comments', set(), general_comments)

            filediff_pks = {
                comment['filediff_id']
                for comment in diff_comments_norm
            }

            filediffs = {
                filediff.pk: filediff
                for filediff in FileDiff.objects.filter(
                    pk__in=filediff_pks,
                    diffset__history__review_request=review_request
                )
            }

            for comment in diff_comments_norm:
                filediff_id = comment.pop('filediff_id')

                try:
                    comment['filediff'] = filediffs[filediff_id]
                    comment['interfilediff'] = None
                except KeyError:
                    return INVALID_FORM_DATA, {
                        'fields': {
                            'diff_comments': [
                                'Invalid filediff ID: %s' % filediff_id,
                            ],
                        },
                    }
        except InvalidFormDataError as e:
            return INVALID_FORM_DATA, e.data

        new_review = Review.objects.create(
            review_request=review_request,
            user=request.user,
            body_top=body_top,
            body_top_rich_text=body_top_rich_text,
            body_bottom=body_bottom,
            body_bottom_rich_text=body_bottom_rich_text,
            ship_it=ship_it)

        for comment_type, comments in (
            (new_review.comments, diff_comments_norm),
            (new_review.general_comments, general_comments_norm)):
            for comment in comments:
                comment_type.create(**comment)

        new_review.publish(
            user=request.user,
            to_owner_only=to_owner_only)

        return 201, {
            self.item_result_key: new_review,
        }

    @overload
    def _normalize_comments_json(
        self,
        comment_type: Literal['diff_comments'],
        extra_keys: set[str],
        comments: str | None,
    ) -> list[DiffCommentData]:
        ...

    @overload
    def _normalize_comments_json(
        self,
        comment_type: Literal['general_comments'],
        extra_keys: set[str],
        comments: str | None,
    ) -> list[GeneralCommentData]:
        ...

    def _normalize_comments_json(
        self,
        comment_type: str,
        extra_keys: set[str],
        comments: str | None,
    ) -> list[GeneralCommentData]:
        """Normalize all the comments.

        Args:
            comment_type (str):
                Type of the comment.

            extra_keys (set of str):
                Extra comment keys expected beyond the base comment keys.

            comments (str):
                A JSON payload containing the comments.

        Returns:
            list of GeneralCommentData:
            A list of the decoded and normalized comments.

        Raises:
            InvalidFormDataError:
                The comment data is incorrect or missing keys.
        """
        base_comment_keys = {'issue_opened', 'text', 'rich_text'}
        expected_keys = base_comment_keys | extra_keys

        try:
            comments = json.loads(comments or '[]')
        except ValueError:
            raise InvalidFormDataError({
                'fields': {
                    comment_type: 'Malformed JSON.',
                }
            })

        for comment in comments:
            comment_keys = set(comment.keys())
            missing_keys = expected_keys - comment_keys

            if missing_keys:
                missing_keys = ', '.join(missing_keys)

                raise InvalidFormDataError({
                    'fields': {
                        comment_type: [
                            f'Element missing keys "{missing_keys}".'
                        ],
                    },
                })

            for key in comment_keys:
                if key not in expected_keys:
                    logging.warning('%s field ignored.', key)
                    del comment[key]

            if comment['issue_opened']:
                comment['issue_status'] = BaseComment.OPEN
            else:
                comment['issue_status'] = None

        return comments


review_bot_review_resource = ReviewBotReviewResource()
