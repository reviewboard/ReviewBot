from __future__ import absolute_import
import json
import pkg_resources

from celery.worker.control import Panel
from reviewbot.celery import celery
from rbtools.api.client import RBClient

from reviewbot.processing.review import Review

# TODO: Make the cookie file configurable.
COOKIE_FILE = 'reviewbot-cookies.txt'
# TODO: Include version information in the agent.
AGENT = 'ReviewBot'


@celery.task(ignore_result=True)
def ProcessReviewRequest(payload, tool_settings):
    """Execute an automated review on a review request."""
    try:
        api_client = RBClient(
            payload['url'] + 'api/',
            cookie_file=COOKIE_FILE,
            username=payload['user'],
            password=payload['password'],
            agent='ReviewBot')
        api_root = api_client.get_root()
    except:
        return False

    routing_key = ProcessReviewRequest.request.delivery_info['routing_key']
    ep_name = routing_key.partition('.')[0]
    tools = []
    for ep in pkg_resources.iter_entry_points(group='reviewbot.tools',
                                              name=ep_name):
        tools.append(ep.load())

    if len(tools) != 1:
        # There was either no Tool, or too many tools.
        # TODO: Properly report the errors.
        return False

    tool = tools[0]
    try:
        review = Review(api_root, payload['request'], payload['settings'])
        t = tool(review, settings=tool_settings)
        t.execute()
        review.publish()
    except:
        # Something went wrong with this tool.
        # TODO: Stop ignoring errors and do something
        # about them.
        return False

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
