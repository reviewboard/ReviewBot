import json
import tornado.web

from reviewbot.processing import tasks


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("ReviewBot, the automated code reviewer")


class PublishedHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("")

    def post(self):

        # Retrieve the payload.
        try:
            request_payload = self.get_argument("payload")
            review_request_info = json.loads(request_payload)
        except:
            self._bad_request()
            return

        # Check to make sure we have the proper data.
        if ('review_request_id' not in review_request_info or
           'new' not in review_request_info or
           'fields_changed' not in review_request_info):
            self._bad_request()
            return

        self.write("")
        self.finish()

        request_id = review_request_info['review_request_id']
        fields_changed = review_request_info['fields_changed']
        new = review_request_info['new']
        diff_info = {'has_diff': False}
        # If a new diff has been uploaded, get the id.
        if not review_request_info['new']:
            try:
                diff_id = fields_changed['diff']['added'][0][2]
                diff_revision_string = fields_changed['diff']['added'][0][0]
                diff_revision = int(diff_revision_string.lstrip('Diff r'))
                diff_info = {'has_diff': True}
                diff_info['id'] = diff_id
                diff_info['revision'] = diff_revision
            except:
                diff_info = {'has_diff': False}

        try:
            tasks.ProcessReviewRequest.delay(request_id, new, diff_info)
        except:
            print "Couldn't send the task"

        print request_payload

    def _bad_request(self):
        self.set_status(400)
        self.finish()
