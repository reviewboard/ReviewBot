import json

from djblets.webapi.decorators import (webapi_login_required,
                                       webapi_response_errors,
                                       webapi_request_fields)
from djblets.webapi.errors import (DOES_NOT_EXIST,
                                   INVALID_FORM_DATA,
                                   NOT_LOGGED_IN,
                                   PERMISSION_DENIED)

from reviewboard.extensions.base import get_extension_manager
from reviewboard.webapi.decorators import webapi_check_local_site
from reviewboard.webapi.resources import WebAPIResource

from reviewbotext.models import Profile, Tool


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
        extension = EXTENSION_MANAGER.get_enabled_extension(ReviewBotExtension.id)

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


# TODO: continue here
# What's the best way to allow manual execution and querying of status
# with resources. What endpoints do I need and how should they be filtered
# etc. Will need the following things:
#
# - Execution manually from a profile ID and Diff ID
# - Display status for a Diff ID + Review Request ID
#   - What can a particular user ID run for this diff?
#   - What IS currently running for this diff?
#   - What IS currently running for ANY diffs?


class ProfileResource(WebAPIResource):
    """Provides information about tool profiles and allows manual execution.
    """
    name = 'profile'
    allowed_methods = ('GET',)
    model_object_key = 'id'
    uri_object_key = 'profile'

    model = Profile
    name = 'profile'
