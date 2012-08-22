from __future__ import absolute_import
import pkg_resources

from reviewbot.celery import celery
from rbtools.api.client import RBClient

from reviewbot.processing.review import Review


COOKIE_FILE = 'reviewbot-cookies.txt'
AGENT = 'ReviewBot'


@celery.task(ignore_result=True)
def ProcessReviewRequest(payload):
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
        t = tool(review)
        t.execute()
        review.publish()
    except:
        # Something went wrong with this tool.
        # TODO: Stop ignoring errors and do something
        # about them.
        return False

    return True
