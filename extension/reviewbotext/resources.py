import json

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from djblets.db.query import LocalDataQuerySet
from djblets.util.decorators import augment_method_from
from djblets.webapi.decorators import (webapi_login_required,
                                       webapi_request_fields,
                                       webapi_response_errors)
from djblets.webapi.errors import (DOES_NOT_EXIST,
                                   INVALID_FORM_DATA,
                                   NOT_LOGGED_IN,
                                   PERMISSION_DENIED)
from reviewboard.diffviewer.models import FileDiff
from reviewboard.extensions.base import get_extension_manager
from reviewboard.reviews.models import BaseComment, Review
from reviewboard.webapi.decorators import webapi_check_local_site
from reviewboard.webapi.resources import resources, WebAPIResource

from reviewbotext.models import ManualPermission, Profile, Tool, ToolExecution


EXTENSION_MANAGER = get_extension_manager()


class ToolResource(WebAPIResource):
    """Resource for workers to update the installed tools list.

    This API endpoint isn't actually RESTful, and just provides a place
    for workers to "dump" their entire list of installed tools as a single
    POST. A GET request will not actually return a list of tools.
    """
    name = 'tool'
    allowed_methods = ('GET', 'POST',)
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
    def create(self, request, hostname, tools, *args, **kwargs):
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
        extension = EXTENSION_MANAGER.get_enabled_extension(
            ReviewBotExtension.id)

        # Ensure the request is from the Review Bot user
        if request.user.id != extension.settings['user']:
            return PERMISSION_DENIED

        try:
            tools = json.loads(tools)
        except:
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
                })

            if not created and not obj.in_last_update:
                obj.in_last_update = True
                obj.save()

        # TODO: Fix the result key here.
        return 201, {}


tool_resource = ToolResource()


class ToolExecutionResource(WebAPIResource):
    """Provides information on an execution of a tool profile.

    This resource contains information about a tool (with a selected profile)
    that is currently being executed or has been executed on a diff revision of
    a review request.

    A tool profile can be executed on the same diff revision of a review
    request multiple times, provided that all previous executions failed or
    timed-out. A new ToolExecution object is created for every execution
    attempt, so we can keep track of information like the number of attempts.
    """
    name = 'tool_execution'
    model = ToolExecution
    model_object_key = 'id'
    uri_object_key = 'tool_execution_id'

    fields = {
        'id': {
            'type': int,
            'description': 'The ID of the tool execution.',
        },
        'profile_id': {
            'type': int,
            'description': 'The ID of the tool profile being executed.',
        },
        'status': {
            'type': ('Q', 'R', 'S', 'F', 'T'),
            'description': 'The current status of the tool execution.',
        },
        'result': {
            'type': str,
            'description': 'A JSON payload containing the result of the tool '
                           'execution. If the execution succeeded, this will '
                           'contain the review. If the execution failed, this '
                           'will contain the error message for the failure.',
        },
        'last_updated': {
            'type': str,
            'description': 'The date and time that the tool execution was '
                           'last updated by the worker executing the tool '
                           'profile.',
        },
    }
    last_modified_field = 'last_updated'

    allowed_methods = ('GET', 'POST', 'PUT')

    def has_access_permissions(self, request, tool_execution, *args, **kwargs):
        return _review_request_is_accessible(
            request,
            tool_execution.review_request_id,
            tool_execution.diff_revision,
            *args, **kwargs)

    def has_list_access_permissions(self, request, *args, **kwargs):
        return _review_request_is_accessible(
            request,
            request.GET.get('review-request-id'),
            request.GET.get('diff-revision'),
            *args, **kwargs)

    def has_modify_permissions(self, request, *args, **kwargs):
        from reviewbotext.extension import ReviewBotExtension
        extension = EXTENSION_MANAGER.get_enabled_extension(
            ReviewBotExtension.id)

        # Only Review Bot workers should be able to update tool executions with
        # their execution status and/or result.
        if request.user.id == extension.settings['user']:
            return True

        return False

    def has_create_permissions(self, request, review_request, profile, *args,
                               **kwargs):
        from reviewbotext.extension import ReviewBotExtension
        extension = EXTENSION_MANAGER.get_enabled_extension(
            ReviewBotExtension.id)

        user = request.user

        # The Review Bot user should have permission.
        if user.id == extension.settings['user']:
            return True

        if not review_request.is_accessible_by(user):
            return False

        local_site = self._get_local_site(kwargs.get('local_site_name'))
        is_admin = user.is_superuser
        is_submitter = (user == review_request.submitter)
        is_in_manual_group = ManualPermission.objects.filter(
            user=user, local_site=local_site, allow=True).exists()

        if ((profile.allow_manual and is_admin) or
            (profile.allow_manual_submitter and is_submitter) or
            (profile.allow_manual_group and is_in_manual_group)):
            return True

        return False

    def get_queryset(self, request, is_list=False, *args, **kwargs):
        """Returns a queryset for ToolExecution models.

        By default, this returns all tool executions.

        If the queryset is being used for a list of tool execution resources,
        this is filtered for tool executions matching the given review request
        ID and diff revision arguments. This can be further filtered by the
        optional arguments.
        """
        if is_list:
            review_request_id = request.GET.get('review-request-id')
            diff_revision = request.GET.get('diff-revision')

            q = Q()

            if 'status' in request.GET:
                statuses = request.GET.get('status').split(',')

                for status in statuses:
                    if status in (u'Q', u'R', u'S', u'F', u'T'):
                        q = q | Q(status=status)

            queryset = self.model.objects.filter(
                q,
                review_request_id=review_request_id,
                diff_revision=diff_revision)

            if 'get-latest' in request.GET:
                get_latest = request.GET.get('get-latest')

                if get_latest in ('1', 'true', 'True'):
                    # Get the last-updated tool executions for unique profiles.
                    # This will be used to display the status of each executed
                    # tool profile in the manual execution UI.
                    # Note: We cannot use distinct(profile__id) since it is
                    # only supported on PostgreSQL. Instead, we make use of the
                    # fact that ToolExecution objects are ordered by
                    # last_updated descending.
                    profiles = set()
                    tool_executions = []

                    for tool_execution in queryset:
                        profile = tool_execution.profile.id

                        if profile not in profiles:
                            profiles.add(profile)
                            tool_executions.append(tool_execution)

                    queryset = LocalDataQuerySet(tool_executions)

            return queryset
        else:
            return self.model.objects.all()

    @webapi_check_local_site
    @webapi_response_errors(PERMISSION_DENIED)
    @webapi_request_fields(
        required={
            'review-request-id': {
                'type': int,
                'description': 'The ID of the review request.',
            },
            'diff-revision': {
                'type': int,
                'description': 'The diff revision of the review request.',
            },
        },
        optional={
            'status': {
                'type': str,
                'description': 'Filter tool executions by one or more '
                               'comma-separated execution statuses.',
            },
            'get-latest': {
                'type': bool,
                'description': 'Whether only the latest tool executions for '
                               'each profile will be listed.',
            },
        },
    )
    @augment_method_from(WebAPIResource)
    def get_list(self, request, *args, **kwargs):
        """Returns all tool executions on a diff revision of a review request.

        The resulting list can be further filtered down to match a given set of
        execution statuses, or to return only the latest tool execution for
        each profile.
        """
        pass

    @webapi_check_local_site
    @webapi_response_errors(DOES_NOT_EXIST, PERMISSION_DENIED)
    @augment_method_from(WebAPIResource)
    def get(self, request, *args, **kwargs):
        """Returns information on a particular tool execution.

        This will include the ID of the profile being executed, the execution
        status, the date and time the worker executing the tool last checked
        in, and the result of the execution (if any).
        """
        pass

    @webapi_login_required
    @webapi_check_local_site
    @webapi_response_errors(DOES_NOT_EXIST, NOT_LOGGED_IN, PERMISSION_DENIED)
    @webapi_request_fields(
        required={
            'review_request_id': {
                'type': int,
                'description': 'The ID of the review request.',
            },
            'diff_revision': {
                'type': int,
                'description': 'The diff revision of the review request.',
            },
            'profile_id': {
                'type': int,
                'description': 'The ID of the tool profile to execute.',
            },
        },
    )
    def create(self, request, review_request_id, diff_revision, profile_id,
               *args, **kwargs):
        """Creates a new tool execution, and adds it to the message queue.

        The tool execution will be created only if there are no previous
        executions of the given profile, or if all previous executions failed
        or timed out.

        After this, an execution request (containing the tool execution ID,
        tool profile ID, review request ID, and diff revision) will be added to
        the message queue.
        """
        # Check that the review request, diff revision, and profile all exist.
        try:
            review_request = resources.review_request.get_object(
                request, review_request_id=review_request_id, *args, **kwargs)
        except ObjectDoesNotExist:
            return DOES_NOT_EXIST

        if not _diff_revision_exists(review_request, diff_revision):
            return DOES_NOT_EXIST

        try:
            profile = Profile.objects.get(pk=profile_id)
        except ObjectDoesNotExist:
            return DOES_NOT_EXIST

        if not self.has_create_permissions(request, review_request, profile):
            return self._no_access_error(request.user)

        # Check that there isn't already a queued/running/succeeded tool
        # execution. We only allow a re-try if previous tool executions failed
        # or timed-out.
        execution_exists = self.model.objects.filter(
            Q(status='Q') | Q(status='R') | Q(status='S'),
            profile=profile,
            review_request_id=review_request_id,
            diff_revision=diff_revision).exists()

        if execution_exists:
            return 409, {}

        tool_execution = self.model.objects.create(
            profile=profile,
            review_request_id=review_request_id,
            diff_revision=diff_revision,
            status='Q')
        tool_execution.save()

        from reviewbotext.extension import ReviewBotExtension
        extension = EXTENSION_MANAGER.get_enabled_extension(
            ReviewBotExtension.id)

        # Add the tool execution request to the message queue.
        request_payload = {
            'tool_execution_id': tool_execution.id,
            'tool_profile_id': profile_id,
            'review_request_id': review_request_id,
            'diff_revision': diff_revision,
        }

        extension.notify(request_payload)

        return 201, {
            self.item_result_key: tool_execution,
        }

    @webapi_login_required
    @webapi_check_local_site
    @webapi_response_errors(DOES_NOT_EXIST, NOT_LOGGED_IN, PERMISSION_DENIED)
    @webapi_request_fields(
        optional={
            'status': {
                'type': ('Q', 'R', 'S', 'F', 'T'),
                'description': 'The status of the tool execution.',
            },
            'result': {
                'type': str,
                'description': 'A JSON payload containing the result of the '
                               'tool execution.',
            },
        },
    )
    def update(self, request, *args, **kwargs):
        """Updates an existing tool execution.

        Only Review Bot workers are allowed to update a tool execution's
        information.

        The last-updated time will automatically be updated upon a PUT request.
        Optionally, the worker can update the execution status, or store the
        result of the execution (the completed review or error details) as a
        JSON blob.
        """
        if not self.has_modify_permissions(request):
            return self._no_access_error(request.user)

        try:
            tool_execution = self.get_object(request, *args, **kwargs)
        except ObjectDoesNotExist:
            return DOES_NOT_EXIST

        for field in ('status', 'result'):
            value = kwargs.get(field, None)

            if value is not None:
                setattr(tool_execution, field, value)

        tool_execution.save()

        return 200, {
            self.item_result_key: tool_execution,
        }


tool_execution_resource = ToolExecutionResource()


class ToolExecutableResource(WebAPIResource):
    """Provides information on executable tool profiles.

    This resource allows us to get a list of tool profiles that the user can
    manually execute on the given diff revision of a review request. A tool
    profile is executable if the user has manual permissions for it, and if
    there are no existing tool executions or if all previous tool executions
    failed or timed out.
    """
    name = 'tool_executable'
    model = Profile
    model_object_key = 'id'

    fields = {
        'id': {
            'type': int,
            'description': 'The ID of the tool profile.',
        },
        'name': {
            'type': str,
            'description': 'The name of the tool profile.',
        },
    }

    allowed_methods = ('GET',)

    def has_list_access_permissions(self, request, *args, **kwargs):
        return _review_request_is_accessible(
            request,
            request.GET.get('review-request-id'),
            request.GET.get('diff-revision'),
            *args, **kwargs)

    def get_queryset(self, request, *args, **kwargs):
        """Returns a queryset containing all executable tool profiles."""
        user = request.user
        review_request_id = request.GET.get('review-request-id')
        diff_revision = request.GET.get('diff-revision')
        local_site = self._get_local_site(kwargs.get('local_site_name'))

        is_admin = user.is_superuser
        is_submitter = (user == resources.review_request.get_object(
            request, review_request_id=review_request_id, *args, **kwargs
            ).submitter)
        is_in_manual_group = ManualPermission.objects.filter(
            user=user, local_site=local_site, allow=True).exists()

        if not (is_admin or is_submitter or is_in_manual_group):
            # The user is not allowed to manually execute any tools, so return
            # an empty queryset.
            return Profile.objects.none()

        q = Q()

        if is_admin:
            q = q | Q(allow_manual=True)

        if is_submitter:
            q = q | Q(allow_manual_submitter=True)

        if is_in_manual_group:
            q = q | Q(allow_manual_group=True)

        queryset = Profile.objects.filter(q, local_site=local_site)

        # Now that we have all Profiles that the user has permission to
        # manually execute, we need to exclude the Profiles that are currently
        # being executed or have already been executed (on this review request
        # and diff).
        queryset = queryset.exclude(
            (Q(toolexecution__review_request_id=review_request_id) &
             Q(toolexecution__diff_revision=diff_revision)) &
            (Q(toolexecution__status='Q') |
             Q(toolexecution__status='R') |
             Q(toolexecution__status='S'))
        )

        return queryset

    def get_serializer_for_object(self, obj):
        return self

    @webapi_login_required
    @webapi_check_local_site
    @webapi_response_errors(NOT_LOGGED_IN, PERMISSION_DENIED)
    @webapi_request_fields(
        required={
            'review-request-id': {
                'type': int,
                'description': 'The ID of the review request.',
            },
            'diff-revision': {
                'type': int,
                'description': 'The diff revision of the review request.',
            },
        },
    )
    @augment_method_from(WebAPIResource)
    def get_list(self, request, *args, **kwargs):
        """Returns a list of executable tool profiles.

        For some given review request and diff revision, a tool profile is
        executable if the user has manual permissions for it, and if there are
        no existing tool executions or if all previous tool executions failed
        or timed out.

        Each tool profile has rules on who can manually execute it (admins,
        the submitter of the review request, users in the ManualPermission
        group).
        """
        pass


tool_executable_resource = ToolExecutableResource()


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
            'body_bottom': {
                'type': str,
                'description': 'The review content below the comments.',
            },
            'diff_comments': {
                'type': str,
                'description': 'A JSON payload containing the diff comments.',
            },
        },
    )
    def create(self, request, review_request_id, ship_it=False, body_top='',
               body_bottom='', diff_comments=None, *args, **kwargs):
        """Creates a new review and publishes it."""
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


def _review_request_is_accessible(request, review_request_id, diff_revision,
                                  *args, **kwargs):
    """Returns True if the user has access to the review request and diff.

    If the review request or the diff revision does not exist, we return False.
    """
    try:
        review_request = resources.review_request.get_object(
            request, review_request_id=review_request_id, *args, **kwargs)
    except ObjectDoesNotExist:
        return False

    if not _diff_revision_exists(review_request, diff_revision):
        return False

    return review_request.is_accessible_by(request.user)


def _diff_revision_exists(review_request, diff_revision):
    """Returns True if the diff revision for the review request exists."""
    num_diffs = review_request.diffset_history.diffsets.get_query_set().count()
    diff_revision = int(diff_revision)

    if diff_revision <= 0 or diff_revision > num_diffs:
        return False

    return True
