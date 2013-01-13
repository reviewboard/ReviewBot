import json

from reviewbot.processing.filesystem import cleanup_tempfiles, make_tempfile


class File(object):
    """Represents a file in the review.

    Information about the file can be retreived through this class,
    including retrieving the actual body of the original or patched
    file.

    Allows comments to be made to the file in the review.
    """
    def __init__(self, review, api_filediff):
        self.review = review
        self.id = int(api_filediff.id)
        self.source_file = api_filediff.source_file
        self.dest_file = api_filediff.dest_file
        self.diff_data = api_filediff.get_diff_data()
        self._api_filediff = api_filediff

    @property
    def patched_file_contents(self):
        # TODO: Cache the contents.
        if not hasattr(self._api_filediff, 'get_patched_file'):
            return None

        patched_file = self._api_filediff.get_patched_file()
        return patched_file.data

    @property
    def original_file_contents(self):
        # TODO Cache the contents
        if not hasattr(self._api_filediff, 'get_original_file'):
            return None

        original_file = self._api_filediff.get_original_file()
        return original_file.data

    def get_patched_file_path(self):
        contents = self.patched_file_contents
        if contents:
            return make_tempfile(contents)
        else:
            return None

    def get_original_file_path(self):
        contents = self.original_file_contents
        if contents:
            return make_tempfile(contents)
        else:
            return None

    def comment(self, text, first_line, num_lines=1, issue=None,
                        original=False):
        """Make a comment on the file.

        If original is True, the line number will correspond to the
        original file, instead of the patched file.
        """
        real_line = self._translate_line_num(first_line)
        modified = self._is_modified(first_line, num_lines)
        if issue is None:
            issue = self.review.settings['open_issues']

        if modified or self.review.settings['comment_unmodified']:
            if issue:
                self.review.ship_it = False

            self._comment(text, real_line, num_lines, issue)

    def _comment(self, text, first_line, num_lines, issue):
        """Add a comment to the list of comments."""
        data = {
            'filediff_id': self.id,
            'first_line': first_line,
            'num_lines': num_lines,
            'text': text,
            'issue_opened': issue,
        }
        self.review.comments.append(data)

    def _translate_line_num(self, line_num, original=False):
        """Convert a file line number to a filediff line number.

        If original is True, will convert based on the original
        file numbers, instead of the patched.

        TODO: Convert to a faster search algorithm.
        """
        line_num_index = 4
        if original:
            line_num_index = 1

        for chunk in self.diff_data.chunks:
            for row in chunk.lines:
                if row[line_num_index] == line_num:
                    return row[0]

    def _is_modified(self, line_num, num_lines, original=False):
        """Indicates if the filediff row is modified or new.

        Will return True if the row is modified, or new, false
        otherwise

        TODO: Convert to a faster search algorithm.

        TODO: Change this to check all chunks within a range for a
        modification. Currently the pep8 tool will only single line
        comment, but future tools might multi-line.
        """
        line_num_index = 4
        if original:
            line_num_index = 1

        for chunk in self.diff_data.chunks:
            for row in chunk.lines:
                if row[line_num_index] == line_num:
                    return not (chunk.change == 'equal')


class Review(object):
    ship_it = False
    body_top = ""
    body_bottom = ""

    def __init__(self, api_root, request, settings):
        self.api_root = api_root
        self.settings = settings
        self.request_id = request['review_request_id']
        self.diff_revision = request.get('diff_revision', None)
        self.comments = []
        self.ship_it = self.settings['ship_it']

        # Get the list of files.
        self.files = []
        if self.diff_revision:
            files = api_root.get_files(review_request_id=self.request_id,
                                       diff_revision=self.diff_revision)
            try:
                while True:
                    for f in files:
                        self.files.append(File(self, f))

                    files = files.get_next()
            except StopIteration:
                pass

    def publish(self):
        """Upload the review to Review Board."""
        # Truncate comments to the maximum permitted amount to avoid
        # overloading the review and freezing the browser.
        max_comments = self.settings['max_comments']
        if len(self.comments) >  max_comments:
            warning = ("WARNING: Number of comments exceeded maximum, "
                       "showing %d of %d.") % (max_comments, len(self.comments))
            self.body_top = "%s\n%s" % (self.body_top, warning)
            del self.comments[max_comments:]

        cleanup_tempfiles()

        try:
            bot_reviews = self.api_root.get_extension(
                extension_name='reviewbotext.extension.ReviewBotExtension'
            ).get_review_bot_reviews()
            bot_reviews.create(
                review_request_id=self.request_id,
                ship_it=self.ship_it,
                body_top=self.body_top,
                body_bottom=self.body_bottom,
                diff_comments=json.dumps(self.comments))
            return True
        except:
            return False
