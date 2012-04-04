from celery.task import task

from reviewbot.processing.api import APIError, ReviewBoardServer
from reviewbot.processing.review import Review
from reviewbot.tools.pep8 import pep8Tool


@task(ignore_result=True)
def ProcessReviewRequest(payload):
    url = 'http://localhost:8080/'
    cookie_file = 'reviewbot-cookies.txt'

    try:
        server = ReviewBoardServer(url, cookie_file, payload['user'],
                                   payload['password'])
        server.check_api_version()
        server.login()
    except:
        return False

    if not payload['request']['has_diff']:
        return True

    try:
        review = Review(server, payload['request'])
    except:
        # Something went wrong when creating the review,
        # just give up.
        return False

    # Put some bogus values in to test
    review.body_top = "This is a Review from Review Bot"

    # Put some bogus comments in.
    for file in review.files:
        pep8Tool(file)

    # Publish the review
    try:
        return review.publish()
    except:
        return False


