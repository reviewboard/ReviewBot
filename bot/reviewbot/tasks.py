from __future__ import absolute_import, unicode_literals

import json
import logging
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

logger = get_task_logger('WORKER')

# Tool execution statuses.
RUNNING = 'R'
SUCCEEDED = 'S'
FAILED = 'F'


@celery.task(ignore_result=True)
def ProcessReviewRequest(server_url,
                         session,
                         review_request_id,
                         diff_revision,
                         tool_execution_id,
                         review_settings,
                         tool_settings):
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

        tool_execution_id (int):
            The ID of the ToolExecution model corresponding to this tool
            execution.

        review_settings (dict):
            Settings for how the review should be created.

        tool_settings (dict):
            The tool-specific settings.

    Returns:
        bool:
        Whether the task completed successfully.
    """
    routing_key = ProcessReviewRequest.request.delivery_info['routing_key']
    route_parts = routing_key.partition('.')
    tool_ep = route_parts[0]
    logger.info('Request to execute review tool "%s" for %s',
                tool_ep, server_url)

    try:
        logger.info('Initializing RB API')
        api_client = RBClient(server_url,
                              cookie_file=COOKIE_FILE,
                              agent=AGENT,
                              session=session)
        api_root = api_client.get_root()
    except:
        logger.error('Could not contact RB server at "%s"', server_url)
        return False

    def _update_tool_execution(status, message):
        if not (status or message):
            return True

        if status == FAILED:
            logger.error(message)
            message = json.dumps({
                'error': message,
            })
        elif status == SUCCEEDED:
            logger.info('Updateding tool execution with completed review')

        try:
            executions = \
                _get_extension_resource(api_root).get_tool_executions(
                    review_request_id, diff_revision)
            tool_execution = executions.get_item(tool_execution_id)
            tool_execution.update(status=status, result=message)
            return True
        except Exception as e:
            logger.exception('Error updating tool execution: %s', e)
            return False

    logger.info('Loading requested tool "%s"', tool_ep)
    tools = []
    for ep in pkg_resources.iter_entry_points(group='reviewbot.tools',
                                              name=tool_ep):
        tools.append(ep.load())

    if len(tools) > 1:
        _update_tool_execution(tool_execution_id, status=FAILED,
                               msg='Tool "%s" is ambiguous' % tool_ep)
        return False
    elif len(tools) == 0:
        _update_tool_execution(tool_execution_id, status=FAILED,
                               msg='Tool "%s" not found' % tool_ep)
        return False

    tool = tools[0]
    try:
        logger.info('Initializing review')
        review = Review(api_root, review_request_id, diff_revision,
                        review_settings)
    except Exception as e:
        _update_tool_execution(tool_execution_id, status=FAILED,
                               msg='Error initializing review: %s' % str(e))
        return False

    try:
        logger.info('Initializing tool "%s" version "%s"',
                    tool.name, tool.version)
        t = tool()

    except Exception as e:
        _update_tool_execution(tool_execution_id, status=FAILED,
                               msg='Error initializing tool: %s' % str(e))
        return False

    try:
        logger.info('Executing tool "%s"', t.name)
        _update_tool_execution(tool_execution_id, status=RUNNING)
        t.execute(review, settings=tool_settings)
        logger.info('Tool execution completed successfully')
    except Exception as e:
        _update_tool_execution(tool_execution_id, status=FAILED,
                               msg='Error executing tool: %s' % str(e))
        return False

    updated = _update_tool_execution(tool_execution_id, status=SUCCEEDED)

    if not updated:
        return False

    try:
        logger.info('Publishing review')
        review.publish()
    except Exception as e:
        _update_tool_execution(tool_execution_id, status=FAILED,
                               msg='Error publishing review: %s' % str(e))
        return False

    logger.info('Review completed successfully')
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
    logging.info('Request to refresh installed tools from "%s"',
                 payload['url'])

    logging.info('Iterating Tools')
    tools = []

    for ep in pkg_resources.iter_entry_points(group='reviewbot.tools'):
        entry_point = ep.name
        tool_class = ep.load()
        tool = tool_class()
        logging.info('Tool: %s' % entry_point)

        if tool.check_dependencies():
            tools.append({
                'name': tool_class.name,
                'entry_point': entry_point,
                'version': tool_class.version,
                'description': tool_class.description,
                'tool_options': json.dumps(tool_class.options),
            })
        else:
            logging.warning('%s dependency check failed.', ep.name)

    logging.info('Done iterating Tools')
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
        logging.error('Could not reach RB server: %s', str(e))
        return {'error': 'Could not reach RB server.'}

    try:
        api_tools = _get_extension_resource(api_root).get_tools()

        api_tools.create(hostname=hostname, tools=tools)
    except Exception as e:
        logging.error('Problem POSTing tools: %s', str(e))
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
