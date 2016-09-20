from __future__ import absolute_import, unicode_literals

import json
import pkg_resources

from celery.utils.log import get_task_logger
from celery.worker.control import Panel
from reviewbot.celery import celery
from rbtools.api.client import RBClient

from reviewbot.processing.review import Review


# TODO: Make the cookie file configurable.
COOKIE_FILE = 'reviewbot-cookies.txt'


# TODO: Include version information in the agent.
AGENT = 'ReviewBot'


# Status Update states
PENDING = 'pending'
DONE_SUCCESS = 'done-success'
DONE_FAILURE = 'done-failure'
ERROR = 'error'


logger = get_task_logger(__name__)


@celery.task(ignore_result=True)
def RunTool(server_url,
            session,
            review_request_id,
            diff_revision,
            changedesc_id,
            review_settings,
            tool_options):
    """Execute an automated review on a review request.

    Args:
        server_url (unicode):
            The URL of the Review Board server.

        session (unicode):
            The encoded session identifier.

        review_request_id (int):
            The ID of the review request being reviewed (ID for use in the
            API, which is the "display_id" field).

        diff_revision (int):
            The ID of the diff revision being reviewed.

        changedesc_id (int):
            The ID of the change description which corresponds to the diff
            revision, if any.

        review_settings (dict):
            Settings for how the review should be created.

        tool_options (dict):
            The tool-specific settings.

    Returns:
        bool:
        Whether the task completed successfully.
    """
    routing_key = RunTool.request.delivery_info['routing_key']
    route_parts = routing_key.partition('.')
    tool_name = route_parts[0]

    log_detail = ('(server=%s, review_request_id=%s, diff_revision=%s)'
                  % (server_url, review_request_id, diff_revision))

    logger.info('Running tool "%s" %s', tool_name, log_detail)

    try:
        logger.info('Initializing RB API %s', log_detail)
        api_client = RBClient(server_url,
                              cookie_file=COOKIE_FILE,
                              agent=AGENT,
                              session=session)
        api_root = api_client.get_root()
    except Exception as e:
        logger.error('Could not contact Review Board server: %s %s',
                     e, log_detail)
        return False

    logger.info('Loading requested tool "%s" %s', tool_name, log_detail)
    tools = [
        entrypoint.load()
        for entrypoint in pkg_resources.iter_entry_points(
            group='reviewbot.tools', name=tool_name)
    ]

    if len(tools) == 0:
        logger.error('Tool "%s" not found %s', tool_name, log_detail)
        return False
    elif len(tools) > 1:
        logger.error('Tool "%s" is ambiguous (found %s) %s',
                     tool_name, ', '.join(tool.name for tool in tools),
                     log_detail)
        return False
    else:
        tool = tools[0]

    try:
        logger.info('Creating status update %s', log_detail)
        review_request = api_root.get_review_request(
            review_request_id=review_request_id)
        status_update = review_request.get_status_updates().create(
            service_id='reviewbot.%s' % tool.name,
            summary=tool.name,
            change_id=changedesc_id,
            state='pending',
            description='running...')
    except Exception as e:
        logger.exception('Unable to create status update: %s %s',
                         e, log_detail)
        return False

    try:
        logger.info('Initializing review %s', log_detail)
        review = Review(api_root, review_request_id, diff_revision,
                        review_settings)
    except Exception as e:
        logger.exception('Failed to initialize review: %s %s', e, log_detail)
        status_update.update(state=ERROR, description='internal error.')
        return False

    try:
        logger.info('Initializing tool "%s %s" %s',
                    tool.name, tool.version, log_detail)
        t = tool()
    except Exception as e:
        logger.exception('Error initializing tool "%s": %s %s',
                         tool.name, e, log_detail)
        status_update.update(state=ERROR, description='internal error.')
        return False

    try:
        logger.info('Executing tool "%s" %s', tool.name, log_detail)
        t.execute(review, settings=tool_options)
        logger.info('Tool "%s" completed successfully %s',
                    tool.name, log_detail)
    except Exception as e:
        logger.exception('Error executing tool "%s": %s %s',
                         tool.name, e, log_detail)
        status_update.update(state=ERROR, description='internal error.')
        return False

    try:
        logger.info('Publishing review %s', log_detail)
        review_id = review.publish().id

        if len(review.comments) == 0:
            new_state = DONE_SUCCESS
            description = 'passed.'
        else:
            new_state = DONE_FAILURE
            description = 'failed.'

        status_update.update(state=new_state,
                             description=description,
                             review_id=review_id)
    except Exception as e:
        logger.exception('Error when publishing review: %s %s', e, log_detail)
        status_update.update(state=ERROR, description='internal error.')
        return False

    logger.info('Review completed successfully %s', log_detail)
    return True


@Panel.register
def update_tools_list(panel, payload):
    """Update the list of installed tools.

    This will detect the installed analysis tool plugins
    and inform Review Board of them.

    Args:
        panel (celery.worker.control.Panel):
            The worker control panel.

        payload (dict):
            The payload as assembled by the extension.

    Returns:
        bool:
        Whether the task completed successfully.
    """
    logger.info('Request to refresh installed tools from "%s"',
                payload['url'])

    logger.info('Iterating Tools')
    tools = []

    for ep in pkg_resources.iter_entry_points(group='reviewbot.tools'):
        entry_point = ep.name
        tool_class = ep.load()
        tool = tool_class()
        logger.info('Tool: %s' % entry_point)

        if tool.check_dependencies():
            tools.append({
                'name': tool_class.name,
                'entry_point': entry_point,
                'version': tool_class.version,
                'description': tool_class.description,
                'tool_options': json.dumps(tool_class.options),
            })
        else:
            logger.warning('%s dependency check failed.', ep.name)

    logger.info('Done iterating Tools')
    tools = json.dumps(tools)
    hostname = panel.hostname

    try:
        api_client = RBClient(
            payload['url'],
            cookie_file=COOKIE_FILE,
            agent=AGENT,
            session=payload['session'])
        api_root = api_client.get_root()
    except Exception as e:
        logger.exception('Could not reach RB server: %s', e)
        return {'error': 'Could not reach RB server.'}

    try:
        api_tools = _get_extension_resource(api_root).get_tools()

        api_tools.create(hostname=hostname, tools=tools)
    except Exception as e:
        logger.exception('Problem POSTing tools: %s', e)
        return {'error': 'Problem POSTing tools.'}

    return {'ok': 'Tool list update complete.'}


def _get_extension_resource(api_root):
    """Return the Review Bot extension resource.

    Args:
        api_root (rbtools.api.resource.Resource):
            The server API root.

    Returns:
        rbtools.api.resource.Resource:
        The extension's API resource.
    """
    # TODO: Cache this. We only use this resource as a link to sub-resources.
    return api_root.get_extension(
        extension_name='reviewbotext.extension.ReviewBotExtension')
