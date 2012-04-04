import pkg_resources

from celery.task import task

from reviewbot.processing.api import APIError, ReviewBoardServer
from reviewbot.processing.review import Review


@task(ignore_result=True)
def ProcessReviewRequest(payload):
    cookie_file = 'reviewbot-cookies.txt'

    try:
        server = ReviewBoardServer(payload['url'], cookie_file,
                                   payload['user'], payload['password'])
        server.check_api_version()
        server.login()
    except:
        return False

    tools = []
    for ep in pkg_resources.iter_entry_points(group='reviewbot.tools'):
        tools.append(ep.load())

    for tool in tools:
        try:
            review = Review(server, payload['request'], payload['settings'])
        except:
            # Something went wrong when creating the review,
            # just ignore it and skip the tool.
            continue

        try:
            tool(review)
        except:
            # Something went wrong with that tool,
            # just ignore it continue.
            continue

        try:
            review.publish()
        except:
            # Something went wrong when publishing,
            # just ignore it and continue.
            continue

    return True
