from celery.task import task

from reviewbot.processing.api import APIError, ReviewBoardServer
from reviewbot.processing.review import Review
from reviewbot.tools.pep8 import pep8Tool


@task(ignore_result=True)
def ProcessReviewRequest(request_id, new, diff_info):
    url = 'http://localhost:8080/'
    cookie_file = 'reviewbot-cookies.txt'
    username = 'reviewbot'
    password = 'reviewbot'

    try:
        server = ReviewBoardServer(url, cookie_file, username, password)
        server.check_api_version()
        server.login()
    except:
        return False

    diff_id = None
    diff_revision = None
    if new:
        # Since the review request is new, we need to check
        # if it has a diff manually (It isn't present in
        # fields_changed).
        try:
            diff_list = server.get_diff_list(request_id)
            for diff in diff_list['diffs']:
                diff_revision = diff['revision']
                diff_id = diff['id']
        except:
            pass
    elif diff_info['has_diff']:
        diff_id = diff_info['id']
        diff_revision = diff_info['revision']

    try:
        review = Review(server, request_id, diff_revision)
    except:
        # Something went wrong when creating the review,
        # just give up.
        return False

    # Put some bogus values in to test
    review.body_top = "This is a Review from Review Bot"
    review.body_bottom = "Request: %s\nNew?: %s" % (
        request_id,
        new,
    )

    # Put some bogus comments in.
    for file in review.files:
        pep8Tool(file)

    # Publish the review
    try:
        return review.publish()
    except:
        return False


