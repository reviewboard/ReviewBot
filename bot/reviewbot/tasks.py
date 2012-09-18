from __future__ import absolute_import
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

logger = get_task_logger("WORKER")


@celery.task(ignore_result=True)
def ProcessReviewRequest(payload, tool_settings):
    """Execute an automated review on a review request."""
    routing_key = ProcessReviewRequest.request.delivery_info['routing_key']
    route_parts = routing_key.partition('.')
    tool_ep = route_parts[0]
    logger.info(
        "Request to execute review tool '%s' for %s" % (
            tool_ep, payload['url']))

    try:
        logger.info("Initializing RB API")
        api_client = RBClient(
            payload['url'] + 'api/',
            cookie_file=COOKIE_FILE,
            username=None,
            password=None,
            agent='ReviewBot',
            session=payload['session'])
        api_root = api_client.get_root()
    except:
        logger.error("Could not contact RB server at '%s'" % payload['url'])
        return False

    logger.info("Loading requested tool '%s'" % tool_ep)
    tools = []
    for ep in pkg_resources.iter_entry_points(group='reviewbot.tools',
                                              name=tool_ep):
        tools.append(ep.load())

    if len(tools) > 1:
        logger.error("Tool '%s' is ambiguous" % tool_ep)
        return False
    elif len(tools) == 0:
        logger.error("Tool '%s' not found" % tool_ep)
        return False

    tool = tools[0]
    try:
        logger.info("Initializing review")
        review = Review(api_root, payload['request'], payload['settings'])
    except Exception, e:
        logger.error("Error initializing review: %s" % str(e))
        return False

    try:
        logger.info("Initializing tool '%s' version '%s'" %
            (tool.name, tool.version))
        t = tool(review, settings=tool_settings)
    except Exception, e:
        logger.error("Error initializing tool: %s" % str(e))
        return False

    try:
        logger.info("Executing tool '%s'" % t.name)
        t.execute()
        logger.info("Tool execution completed successfully")
    except Exception, e:
        logger.error("Error executing tool: %s" % str(e))
        return False

    try:
        logger.info("Publishing review")
        review.publish()
    except Exception, e:
        logger.error("Error publishing review: %s" % str(e))
        return False

    logger.info("Review completed successfully")
    return True


@Panel.register
def update_tools_list(panel, payload):
    """Update the RB server with installed tools.

    This will detect the installed analysis tool plugins
    and inform Review Board of them.
    """
    tools = []
    for ep in pkg_resources.iter_entry_points(group='reviewbot.tools'):
        entry_point = ep.name
        tool = ep.load()
        tools.append({
            'name': tool.name,
            'entry_point': entry_point,
            'version': tool.version,
            'description': tool.description,
            'tool_options': json.dumps(tool.options),
        })

    tools = json.dumps(tools)
    # TODO: Get the actual hostname.
    hostname = 'hostname'

    try:
        api_client = RBClient(
            payload['url'] + 'api/',
            cookie_file=COOKIE_FILE,
            username=payload['user'],
            password=payload['password'],
            agent='ReviewBot')
        api_root = api_client.get_root()
    except:
        return {'error': 'Could not reach RB server.'}

    try:
        api_tools = api_root.get_extension(
            values={
                'extension_name': 'reviewbotext.extension.ReviewBotExtension',
            }).get_review_bot_tools()

        api_tools.create(
            data={
                'hostname': hostname,
                'tools': tools,
            })
    except:
        return {'error': 'Problem POSTing tools.'}

    return {'ok': 'Tool list update complete.'}
