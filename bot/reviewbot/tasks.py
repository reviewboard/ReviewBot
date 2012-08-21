import pkg_resources

from celery.task import task
from rbtools.api.client import RBClient
from rbtools.api.errors import APIError

from reviewbot.processing.review import Review

COOKIE_FILE = 'reviewbot-cookies.txt'
AGENT = 'ReviewBot'


@task(ignore_result=True)
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

    tools = []
    for ep in pkg_resources.iter_entry_points(group='reviewbot.tools'):
        tools.append(ep.load())

    for tool in tools:
        try:
            review = Review(api_root, payload['request'], payload['settings'])
            t = tool(review)
            t.execute()
            review.publish()
        except:
            # Something went wrong with this tool.
            # TODO: Stop ignoring errors and do something
            # about them.
            continue

    return True
