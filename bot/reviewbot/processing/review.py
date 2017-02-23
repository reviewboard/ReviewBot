from __future__ import unicode_literals

import json
import os.path

from rbtools.api.errors import APIError

from reviewbot.utils.filesystem import make_tempfile


class File(object):
    """Represents a file in the review.

    Information about the file can be retreived through this class,
    including retrieving the actual body of the original or patched
    file.

    Allows comments to be made to the file in the review.
    """

    def __init__(self, review, api_filediff):
        """Initialize the File.

        Args:
            review (Review):
                The review object.

            api_filediff (rbtools.api.resource.Resource):
                The filediff resource.
        """
        self.review = review
        self.id = int(api_filediff.id)
        self.source_file = api_filediff.source_file
        self.dest_file = api_filediff.dest_file
        self.diff_data = api_filediff.get_diff_data()
        self._api_filediff = api_filediff
        self.filename, self.file_extension = os.path.splitext(
            api_filediff.dest_file)
        self.patched_file_path = None

    @property
    def patched_file_contents(self):
        """The patched contents of the file.

        Returns:
            bytes:
            The contents of the patched file.
        """
        if not hasattr(self._api_filediff, 'get_patched_file'):
            return None

        patched_file = self._api_filediff.get_patched_file()
        return patched_file.data

    @property
    def original_file_contents(self):
        """The original contents of the file.

        Returns:
            bytes:
            The contents of the original file.
        """
        if not hasattr(self._api_filediff, 'get_original_file'):
            return None

        original_file = self._api_filediff.get_original_file()
        return original_file.data

    def get_patched_file_path(self):
        """Fetch the patched file and return the filename of it.

        Returns:
            unicode:
            The filename of a new temporary file containing the patched file
            contents. If the file is empty, return None.
        """
        if self.patched_file_path:
            return self.patched_file_path
        else:
            try:
                contents = self.patched_file_contents
            except APIError as e:
                if e.http_status == 404:
                    # This was a deleted file.
                    return None
                else:
                    raise

            if contents:
                return make_tempfile(contents, self.file_extension)
            else:
                return None

    def get_original_file_path(self):
        """Fetch the original file and return the filename of it.

        Returns:
            unicode:
            The filename of a new temporary file containing the original file
            contents. If the file is empty, return None.
        """
        contents = self.original_file_contents

        if contents:
            return make_tempfile(contents, self.file_extension)
        else:
            return None

    def comment(self, text, first_line, num_lines=1, issue=None,
                rich_text=False, original=False):
        """Make a comment on the file.

        Args:
            text (unicode):
                The text of the comment.

            first_line (int):
                The line number that the comment starts on.

            num_lines (int, optional):
                The number of lines that the comment should span.

            issue (bool, optional):
                Whether an issue should be opened.

            rich_text (bool, optional):
                Whether the comment text should be formatted using Markdown.

            original (bool, optional):
                If True, the ``first_line`` argument corresponds to the line
                number in the original file, instead of the patched file.
        """
        real_line = self._translate_line_num(first_line)
        modified = self._is_modified(first_line, num_lines)

        if num_lines != 1:
            last_line = first_line + num_lines - 1
            real_last_line = self._translate_line_num(last_line)
            num_lines = real_last_line - real_line + 1

        if issue is None:
            issue = self.review.settings['open_issues']

        if modified or self.review.settings['comment_unmodified']:
            data = {
                'filediff_id': self.id,
                'first_line': real_line,
                'num_lines': num_lines,
                'text': text,
                'issue_opened': issue,
                'rich_text': rich_text,
            }
            self.review.comments.append(data)

    def _translate_line_num(self, line_num, original=False):
        """Convert a file line number to a filediff line number.

        Args:
            line_num (int):
                The line number within the file.

            original (bool, optional):
                If True, the ``line_num`` argument corresponds to the line
                number in the original file, instead of the patched file.

        Returns:
            int:
            The filediff row number.
        """
        # TODO: Convert to a faster search algorithm.
        line_num_index = 4

        if original:
            line_num_index = 1

        for chunk in self.diff_data.chunks:
            for row in chunk.lines:
                if row[line_num_index] == line_num:
                    return row[0]

    def _is_modified(self, line_num, num_lines, original=False):
        """Return whether the given region is modified in the diff.

        Args:
            first_line (int):
                The line number that the comment starts on.

            num_lines (int):
                The number of lines that the comment should span.

            original (bool, optional):
                If True, the ``first_line`` argument corresponds to the line
                number in the original file, instead of the patched file.

        Returns:
            bool:
            True if the region corresponds to modified code.
        """
        # TODO: Convert to a faster search algorithm.

        # TODO: Change this to check all chunks within a range for a
        # modification. Current tools will only comment on single lines, but
        # future tools might create multi-line comments.
        line_num_index = 4

        if original:
            line_num_index = 1

        for chunk in self.diff_data.chunks:
            for row in chunk.lines:
                if row[line_num_index] == line_num:
                    return not (chunk.change == 'equal')


class Review(object):
    """An object which orchestrates the creation of a review."""

    #: Additional text to show above the comments in the review.
    body_top = ""

    #: Additional text to show below the comments in the review.
    body_bottom = ""

    def __init__(self, api_root, review_request_id, diff_revision, settings):
        """Initialize the review.

        Args:
            api_root (rbtools.api.resource.Resource):
                The API root.

            review_request_id (int):
                The ID of the review request being reviewed (ID for use in the
                API, which is the "display_id" field).

            diff_revision (int):
                The diff revision being reviewed.

            settings (dict):
                The settings provided by the extension when triggering the
                task.
        """
        self.api_root = api_root
        self.settings = settings
        self.review_request_id = review_request_id
        self.diff_revision = diff_revision
        self.comments = []

        # Get the list of files.
        self.files = []
        if self.diff_revision:
            files = api_root.get_files(
                review_request_id=self.review_request_id,
                diff_revision=self.diff_revision)

            self.files = [File(self, f) for f in files]

    def publish(self):
        """Upload the review to Review Board."""
        # Truncate comments to the maximum permitted amount to avoid
        # overloading the review and freezing the browser.
        max_comments = self.settings['max_comments']

        if len(self.comments) > max_comments:
            warning = ('**Warning:** Showing %d of %d failures.'
                       % (max_comments, len(self.comments)))

            if self.body_top:
                self.body_top = '%s\n%s' % (self.body_top, warning)
            else:
                self.body_top = warning

            del self.comments[max_comments:]

        bot_reviews = self.api_root.get_extension(
            extension_name='reviewbotext.extension.ReviewBotExtension'
        ).get_review_bot_reviews()

        return bot_reviews.create(
            review_request_id=self.review_request_id,
            body_top=self.body_top,
            body_top_rich_text=True,
            body_bottom=self.body_bottom,
            diff_comments=json.dumps(self.comments))

    @property
    def patch_contents(self):
        """The contents of the patch.

        Returns:
            unicode:
            The contents of the patch associated with the review request and
            diff revision.
        """
        if not hasattr(self, 'patch'):
            if not hasattr(self.api_root, 'get_diff'):
                return None

            self.patch = self.api_root.get_diff(
                review_request_id=self.review_request_id,
                diff_revision=self.diff_revision).get_patch().data

        return self.patch

    def get_patch_file_path(self):
        """Fetch the patch and return the filename of it.

        Returns:
            unicode:
            The filename of a new temporary file containing the patch contents.
            If the patch is empty, return None.
        """
        patch_contents = self.patch_contents

        if patch_contents:
            return make_tempfile(patch_contents, '.diff')
        else:
            return None
