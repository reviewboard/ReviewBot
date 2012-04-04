import base64
import cookielib
import mimetools
import urllib2
from pkg_resources import parse_version
from urlparse import urljoin, urlparse

try:
    # Specifically import json_loads, to work around some issues with
    # installations containing incompatible modules named "json".
    from json import loads as json_loads
except ImportError:
    from simplejson import loads as json_loads


class APIError(Exception):
    def __init__(self, http_status, error_code, rsp=None, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)
        self.http_status = http_status
        self.error_code = error_code
        self.rsp = rsp

    def __str__(self):
        code_str = "HTTP %d" % self.http_status

        if self.error_code:
            code_str += ', API Error %d' % self.error_code

        if self.rsp and 'err' in self.rsp:
            return '%s (%s)' % (self.rsp['err']['msg'], code_str)
        else:
            return code_str


class HTTPRequest(urllib2.Request):
    def __init__(self, url, body='', headers={}, method="PUT"):
        urllib2.Request.__init__(self, url, body, headers)
        self.method = method

    def get_method(self):
        return self.method


class PresetHTTPAuthHandler(urllib2.BaseHandler):
    """urllib2 handler that presets the use of HTTP Basic Auth."""
    handler_order = 480  # After Basic auth

    def __init__(self, url, password_mgr):
        self.url = url
        self.password_mgr = password_mgr
        self.used = False

    def reset(self, username, password):
        self.password_mgr.rb_user = username
        self.password_mgr.rb_pass = password
        self.used = False

    def http_request(self, request):
        if not self.used:
            # Note that we call password_mgr.find_user_password to get the
            # username and password we're working with.
            username, password = \
                self.password_mgr.find_user_password('Web API', self.url)
            raw = '%s:%s' % (username, password)
            request.add_header(
                urllib2.HTTPBasicAuthHandler.auth_header,
                'Basic %s' % base64.b64encode(raw).strip())
            self.used = True

        return request

    https_request = http_request


class ReviewBoardHTTPErrorProcessor(urllib2.HTTPErrorProcessor):
    """Processes HTTP error codes.

    Python 2.6 gets HTTP error code processing right, but 2.4 and 2.5 only
    accepts HTTP 200 and 206 as success codes. This handler ensures that
    anything in the 200 range is a success.
    """
    def http_response(self, request, response):
        if not (200 <= response.code < 300):
            response = self.parent.error('http', request, response,
                                         response.code, response.msg,
                                         response.info())

        return response

    https_response = http_response


class ReviewBoardHTTPBasicAuthHandler(urllib2.HTTPBasicAuthHandler):
    """Custom Basic Auth handler that doesn't retry excessively.

    urllib2's HTTPBasicAuthHandler retries over and over, which is useless.
    This subclass only retries once to make sure we've attempted with a
    valid username and password. It will then fail so we can use
    tempt_fate's retry handler.
    """
    def __init__(self, *args, **kwargs):
        urllib2.HTTPBasicAuthHandler.__init__(self, *args, **kwargs)
        self._retried = False
        self._lasturl = ""

    def retry_http_basic_auth(self, *args, **kwargs):
        if self._lasturl != args[0]:
            self._retried = False

        self._lasturl = args[0]

        if not self._retried:
            self._retried = True
            self.retried = 0
            response = urllib2.HTTPBasicAuthHandler.retry_http_basic_auth(
                self, *args, **kwargs)

            if response.code != 401:
                self._retried = False

            return response
        else:
            return None


class ReviewBoardHTTPPasswordMgr(urllib2.HTTPPasswordMgr):
    """
    Adds HTTP authentication support for URLs.

    Python 2.4's password manager has a bug in http authentication when the
    target server uses a non-standard port.  This works around that bug on
    Python 2.4 installs. This also allows post-review to prompt for passwords
    in a consistent way.

    See: http://bugs.python.org/issue974757
    """
    def __init__(self, reviewboard_url, rb_user=None, rb_pass=None):
        self.passwd = {}
        self.rb_url = reviewboard_url
        self.rb_user = rb_user
        self.rb_pass = rb_pass

    def find_user_password(self, realm, uri):
        if realm == 'Web API':
            return self.rb_user, self.rb_pass
        else:
            # If this is an auth request for some other domain (since HTTP
            # handlers are global), fall back to standard password management.
            return urllib2.HTTPPasswordMgr.find_user_password(self, realm, uri)


class ReviewBoardServer(object):
    """
    An instance of a Review Board server.
    """
    def __init__(self, url, cookie_file, username, password):
        self.url = url
        if self.url[-1] != '/':
            self.url += '/'
        self.root_resource = None
        self.deprecated_api = False
        self.cookie_file = cookie_file
        self.cookie_jar = cookielib.MozillaCookieJar(self.cookie_file)

        if self.cookie_file:
            try:
                self.cookie_jar.load(self.cookie_file, ignore_expires=True)
            except IOError:
                pass

        # Set up the HTTP libraries to support all of the features we need.
        password_mgr = ReviewBoardHTTPPasswordMgr(self.url,
                                                  username,
                                                  password)
        self.preset_auth_handler = PresetHTTPAuthHandler(self.url, password_mgr)

        handlers = []

        handlers += [
            urllib2.HTTPCookieProcessor(self.cookie_jar),
            ReviewBoardHTTPBasicAuthHandler(password_mgr),
            urllib2.HTTPDigestAuthHandler(password_mgr),
            self.preset_auth_handler,
            ReviewBoardHTTPErrorProcessor(),
        ]

        opener = urllib2.build_opener(*handlers)
        opener.addheaders = [
            ('User-agent', 'ReviewBot/' + '0.1'),
        ]
        urllib2.install_opener(opener)

    def check_api_version(self):
        """Checks the API version on the server to determine which to use."""
        try:
            root_resource = self.api_get('api/')
            rsp = self.api_get(root_resource['links']['info']['href'])

            self.rb_version = rsp['info']['product']['package_version']

            if parse_version(self.rb_version) >= parse_version('1.5.2'):
                self.deprecated_api = False
                self.root_resource = root_resource
                return True
        except APIError, e:
            if e.http_status not in (401, 404):
                # We shouldn't reach this. If there's a permission denied
                # from lack of logging in, then the basic auth handler
                # should have hit it.
                #
                # However in some versions it wants you to be logged in
                # and returns a 401 from the application after you've
                # done your http basic auth
                return False

        # This is an older Review Board server with the old API.
        self.deprecated_api = True
        raise Exception("Old API not supported")
        return True

    def login(self, force=False):
        """
        Logs in to a Review Board server, prompting the user for login
        information if needed.
        """
        if self.deprecated_api:
            # Not Supporting this.
            raise Exception("Old API not supported")
        elif force:
            self.preset_auth_handler.reset()

    def has_valid_cookie(self):
        """
        Load the user's cookie file and see if they have a valid
        'rbsessionid' cookie for the current Review Board server.  Returns
        true if so and false otherwise.
        """
        try:
            parsed_url = urlparse(self.url)
            host = parsed_url[1]
            path = parsed_url[2] or '/'

            # Cookie files don't store port numbers, unfortunately, so
            # get rid of the port number if it's present.
            host = host.split(":")[0]

            # Cookie files also append .local to bare hostnames
            if '.' not in host:
                host += '.local'

            try:
                cookie = self.cookie_jar._cookies[host][path]['rbsessionid']

                if not cookie.is_expired():
                    # debug("Loaded valid cookie -- no login required")
                    return True

                # debug("Cookie file loaded, but cookie has expired")
            except KeyError:
                pass
                # debug("Cookie file loaded, but no cookie for this server")
        except IOError:
            pass
            # debug("Couldn't load cookie file: %s" % error)

        return False

    def new_review(self, review_request, body_top="", body_bottom="",
                   ship_it=False, public=False):
        """
        Creates a review on a Review Board server.
        """
        data = {
            'body_top': body_top,
            'body_bottom': body_bottom,
            'public': public,
            'ship_it': ship_it,
        }

        try:
            rsp = self.api_post(
                review_request['links']['reviews']['href'], data)
        except APIError, e:
            raise e

        return rsp

    def publish_review(self, review):
        self.api_put(review['links']['update']['href'], {
            'public': 1,
        })

    def set_review_fields(self, review, data):
        """
        Sets a field in a review to the specified value.
        """
        self.api_put(review['links']['update']['href'], data)

    def get_review_request(self, rid):
        """
        Returns the review request with the specified ID.
        """
        if self.deprecated_api:
            url = 'api/json/reviewrequests/%s/' % rid
        else:
            url = '%s%s/' % (
                self.root_resource['links']['review_requests']['href'], rid)

        rsp = self.api_get(url)

        return rsp['review_request']

    def get_diff_files(self, review_request_id, diff_revision):
        """
        Returns the file list for a diff.
        """
        try:
            files_template = self.root_resource['uri_templates']['files']
            url = files_template.replace(
                '{review_request_id}',
                str(review_request_id)).replace(
                '{diff_revision}',
                str(diff_revision))
            rsp = self.api_get(url)
        except APIError, e:
            raise e

        return rsp

    def get_patched_file(self, review_request_id, diff_revision, filediff_id):
        """
        Returns the contents of the patched file from a filediff.
        """
        try:
            template = self.root_resource['uri_templates']['patched_file']
            url = template.replace(
                '{review_request_id}',
                str(review_request_id)).replace(
                '{diff_revision}',
                str(diff_revision)).replace(
                '{filediff_id}',
                str(filediff_id))
            rsp = self.api_raw_get(url)
        except APIError, e:
            raise e

        return rsp

    def get_diff_data(self, review_request_id, diff_revision, filediff_id):
        """
        Returns the contents of the diff data.
        """
        try:
            file_template = self.root_resource['uri_templates']['file']
            url = file_template.replace(
                '{review_request_id}',
                str(review_request_id)).replace(
                '{diff_revision}',
                str(diff_revision)).replace(
                '{filediff_id}',
                str(filediff_id))
            rsp = self.api_get_mime(url,
                'application/vnd.reviewboard.org.diff.data+json')
        except APIError, e:
            raise e

        return rsp

    def post_diff_comment(self, review_request_id, review_id, data):
        """
        Posts a comment on a diff
        """
        if ('filediff_id' not in data or 'first_line' not in data or
            'num_lines' not in data or 'text' not in data):
            # TODO: Change to a proper exception.
            raise Exception("Data for comment missing required fields")
        try:
            review_template = self.root_resource['uri_templates']['review']
            url = review_template.replace(
                '{review_request_id}',
                str(review_request_id)).replace(
                '{review_id}',
                str(review_id)) + 'diff-comments/'
            self.api_post(url, data)
        except APIError, e:
            raise e

    def get_diff_list(self, review_request_id):
        """
        Returns the list of diffs associated with a review request.
        """
        try:
            diffs_template = self.root_resource['uri_templates']['diffs']
            url = diffs_template.replace('{review_request_id}',
                                         str(review_request_id))
            rsp = self.api_get(url)
        except APIError, e:
            raise e

        return rsp

    def process_json(self, data):
        """
        Loads in a JSON file and returns the data if successful. On failure,
        APIError is raised.
        """
        rsp = json_loads(data)

        if rsp['stat'] == 'fail':
            # With the new API, we should get something other than HTTP
            # 200 for errors, in which case we wouldn't get this far.
            assert self.deprecated_api
            self.process_error(200, data)

        return rsp

    def process_error(self, http_status, data):
        """Processes an error, raising an APIError with the information."""
        try:
            rsp = json_loads(data)

            assert rsp['stat'] == 'fail'

            #debug("Got API Error %d (HTTP code %d): %s" %
            #      (rsp['err']['code'], http_status, rsp['err']['msg']))
            #debug("Error data: %r" % rsp)
            raise APIError(http_status, rsp['err']['code'], rsp,
                           rsp['err']['msg'])
        except ValueError:
            #debug("Got HTTP error: %s: %s" % (http_status, data))
            raise APIError(http_status, None, None, data)

    def http_get(self, path):
        """
        Performs an HTTP GET on the specified path, storing any cookies that
        were set.
        """
        #debug('HTTP GETting %s' % path)

        url = self._make_url(path)
        rsp = urllib2.urlopen(url).read()

        try:
            self.cookie_jar.save(self.cookie_file)
        except IOError, e:
            pass
            #debug('Failed to write cookie file: %s' % e)
        return rsp

    def http_get_mime(self, path, mime):
        """
        Performs an HTTP PUT on the specified path, storing any cookies that
        were set.
        """
        url = self._make_url(path)
        #debug('HTTP PUTting to %s: %s' % (url, fields))

        headers = {
            'Accept': mime,
        }

        try:
            r = HTTPRequest(url, '', headers, method='GET')
            data = urllib2.urlopen(r).read()
            try:
                self.cookie_jar.save(self.cookie_file)
            except IOError, e:
                pass
                #debug('Failed to write cookie file: %s' % e)
            return data
        except urllib2.HTTPError, e:
            # Re-raise so callers can interpret it.
            raise e
        except urllib2.URLError, e:
            try:
                pass
                #debug(e.read())
            except AttributeError:
                pass
            raise e
            #die("Unable to access %s. The host path may be invalid\n%s" % \
                #(url, e))

    def _make_url(self, path):
        """Given a path on the server returns a full http:// style url"""
        if path.startswith('http'):
            # This is already a full path.
            return path

        app = urlparse(self.url)[2]

        if path[0] == '/':
            url = urljoin(self.url, app[:-1] + path)
        else:
            url = urljoin(self.url, app + path)

        if not url.startswith('http'):
            url = 'http://%s' % url
        return url

    def api_get(self, path):
        """
        Performs an API call using HTTP GET at the specified path.
        """
        try:
            return self.process_json(self.http_get(path))
        except urllib2.HTTPError, e:
            self.process_error(e.code, e.read())

    def api_get_mime(self, path, mime):
        """
        Performs an API call using HTTP GET at the specified path.
        """
        try:
            return self.process_json(self.http_get_mime(path, mime))
        except urllib2.HTTPError, e:
            self.process_error(e.code, e.read())


    def api_raw_get(self, path):
        """
        Performs an API call using HTTP GET at the specified path.

        Will return the raw request, instead of processing the JSON.
        """
        try:
            return self.http_get(path)
        except urllib2.HTTPError, e:
            self.process_error(e.code, e.read())

    def http_post(self, path, fields, files=None):
        """
        Performs an HTTP POST on the specified path, storing any cookies that
        were set.
        """
        if fields:
            debug_fields = fields.copy()
        else:
            debug_fields = {}

        if 'password' in debug_fields:
            debug_fields["password"] = "**************"
        url = self._make_url(path)
        #debug('HTTP POSTing to %s: %s' % (url, debug_fields))

        content_type, body = self._encode_multipart_formdata(fields, files)
        headers = {
            'Content-Type': content_type,
            'Content-Length': str(len(body))
        }

        try:
            r = urllib2.Request(str(url), body, headers)
            data = urllib2.urlopen(r).read()
            try:
                self.cookie_jar.save(self.cookie_file)
            except IOError, e:
                pass
                # debug('Failed to write cookie file: %s' % e)
            return data
        except urllib2.HTTPError, e:
            # Re-raise so callers can interpret it.
            raise e
        except urllib2.URLError, e:
            try:
                pass
                #debug(e.read())
            except AttributeError:
                pass

            #die("Unable to access %s. The host path may be invalid\n%s" % \
            #    (url, e))

    def http_put(self, path, fields):
        """
        Performs an HTTP PUT on the specified path, storing any cookies that
        were set.
        """
        url = self._make_url(path)
        #debug('HTTP PUTting to %s: %s' % (url, fields))

        content_type, body = self._encode_multipart_formdata(fields, None)
        headers = {
            'Content-Type': content_type,
            'Content-Length': str(len(body))
        }

        try:
            r = HTTPRequest(url, body, headers, method='PUT')
            data = urllib2.urlopen(r).read()
            try:
                self.cookie_jar.save(self.cookie_file)
            except IOError, e:
                pass
                #debug('Failed to write cookie file: %s' % e)
            return data
        except urllib2.HTTPError, e:
            # Re-raise so callers can interpret it.
            raise e
        except urllib2.URLError, e:
            try:
                pass
                #debug(e.read())
            except AttributeError:
                pass
            raise e
            #die("Unable to access %s. The host path may be invalid\n%s" % \
                #(url, e))

    def http_delete(self, path):
        """
        Performs an HTTP DELETE on the specified path, storing any cookies that
        were set.
        """
        url = self._make_url(path)
        #debug('HTTP DELETing %s' % url)

        try:
            r = HTTPRequest(url, method='DELETE')
            data = urllib2.urlopen(r).read()
            try:
                self.cookie_jar.save(self.cookie_file)
            except IOError, e:
                pass
                #debug('Failed to write cookie file: %s' % e)
            return data
        except urllib2.HTTPError, e:
            # Re-raise so callers can interpret it.
            raise e
        except urllib2.URLError, e:
            try:
                pass
                #debug(e.read())
            except AttributeError:
                pass
            raise e
            #die("Unable to access %s. The host path may be invalid\n%s" % \
            #    (url, e))

    def api_post(self, path, fields=None, files=None):
        """
        Performs an API call using HTTP POST at the specified path.
        """
        try:
            return self.process_json(self.http_post(path, fields, files))
        except urllib2.HTTPError, e:
            self.process_error(e.code, e.read())

    def api_put(self, path, fields=None):
        """
        Performs an API call using HTTP PUT at the specified path.
        """
        try:
            return self.process_json(self.http_put(path, fields))
        except urllib2.HTTPError, e:
            self.process_error(e.code, e.read())

    def api_delete(self, path):
        """
        Performs an API call using HTTP DELETE at the specified path.
        """
        try:
            return self.process_json(self.http_delete(path))
        except urllib2.HTTPError, e:
            self.process_error(e.code, e.read())

    def _encode_multipart_formdata(self, fields, files):
        """
        Encodes data for use in an HTTP POST.
        """
        BOUNDARY = mimetools.choose_boundary()
        content = ""

        fields = fields or {}
        files = files or {}

        for key in fields:
            content += "--" + BOUNDARY + "\r\n"
            content += "Content-Disposition: form-data; name=\"%s\"\r\n" % key
            content += "\r\n"
            content += str(fields[key]) + "\r\n"

        for key in files:
            filename = files[key]['filename']
            value = files[key]['content']
            content += "--" + BOUNDARY + "\r\n"
            content += "Content-Disposition: form-data; name=\"%s\"; " % key
            content += "filename=\"%s\"\r\n" % filename
            content += "\r\n"
            content += value + "\r\n"

        content += "--" + BOUNDARY + "--\r\n"
        content += "\r\n"

        content_type = "multipart/form-data; boundary=%s" % BOUNDARY

        return content_type, content
