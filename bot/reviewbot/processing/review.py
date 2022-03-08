from __future__ import division, unicode_literals

import json
import os
from enum import Enum
from itertools import islice

from rbtools.api.errors import APIError

from reviewbot.utils.filesystem import (ensure_dirs_exist,
                                        make_tempdir,
                                        make_tempfile,
                                        normalize_platform_path)
from reviewbot.utils.log import get_logger


#: The logger for the module.
#:
#: Version Added:
#:     3.0
logger = get_logger(__name__, is_task_logger=False)


class ReviewFileStatus(Enum):
    """The change status of a file.

    Version Added:
        3.0
    """

    CREATED = 'created'
    DELETED = 'deleted'
    MODIFIED = 'modified'
    MOVED = 'moved'
    COPIED = 'copied'

    @classmethod
    def for_filediff(cls, filediff):
        """Return a status for a FileDiff.

        Args:
            filediff (rbtools.api.resource.Resource):
                The filediff resource.

        Returns:
            ReviewFileStatus:
            The resulting status.

        Raises:
            ValueError:
                The status for the FileDiff is unknown/unsupported.
        """
        if filediff.source_revision == 'PRE-CREATION':
            return cls.CREATED
        else:
            return cls(filediff.status)


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
        self.diff_data = api_filediff.get_diff_data()
        self.status = ReviewFileStatus.for_filediff(api_filediff)
        self.patched_file_path = None

        self.source_file = normalize_platform_path(api_filediff.source_file)

        if api_filediff.source_file == api_filediff.dest_file:
            # We don't need to normalize again. Just copy.
            self.dest_file = self.source_file
        else:
            self.dest_file = normalize_platform_path(api_filediff.dest_file)

        self.filename, self.file_extension = os.path.splitext(self.dest_file)

        self._api_filediff = api_filediff

    @property
    def patched_file_contents(self):
        """The patched contents of the file.

        Returns:
            bytes:
            The contents of the patched file.
        """
        if (self.status == ReviewFileStatus.DELETED or
            not hasattr(self._api_filediff, 'get_patched_file')):
            return None

        try:
            return self._api_filediff.get_patched_file().data
        except APIError as e:
            if e.http_status == 404:
                # This was a deleted file, a deleted FileDiff entry,
                # or something has gone wrong with the setup.
                return None
            elif e.http_status == 500:
                # There was an issue with the patch server-side. Likely,
                # there's a failure applying the patch, or an outage
                # with a server. Log and skip.
                logger.warning('Received a HTTP 500 fetching patched '
                               'content for %r: %r',
                               self._api_filediff, e)
                return None

            raise

    @property
    def original_file_contents(self):
        """The original contents of the file.

        Returns:
            bytes:
            The contents of the original file.
        """
        if (self.status == ReviewFileStatus.CREATED or
            not hasattr(self._api_filediff, 'get_original_file')):
            return None

        try:
            return self._api_filediff.get_original_file().data
        except APIError as e:
            if e.http_status == 404:
                # This was a deleted FileDiff entry, or something has gone
                # wrong with the setup.
                return None
            elif e.http_status == 500:
                # There was probably an issue with accessing the repository
                # server-side. Log and skip.
                logger.warning('Received a HTTP 500 fetching original content '
                               'for %r: %r',
                               self._api_filediff, e)
                return None

            raise

    def get_patched_file_path(self):
        """Fetch the patched file and return the filename of it.

        Version Changed:
            3.0:
            Empty files no longer return ``None``.

        Returns:
            unicode:
            The filename of a new temporary file containing the patched file
            contents. If the file is deleted, this will return ``None``.
        """
        if self.patched_file_path:
            return self.patched_file_path

        if self.status == ReviewFileStatus.DELETED:
            return None

        contents = self.patched_file_contents

        # Make sure we don't treat empty files as non-existent at this point.
        if contents is None:
            return None

        tempdir = make_tempdir()
        filename = os.path.join(tempdir, os.path.basename(self.dest_file))

        with open(filename, 'wb') as fp:
            fp.write(contents)

        return filename

    def get_original_file_path(self):
        """Fetch the original file and return the filename of it.

        Version Changed:
            3.0:
            Empty files no longer return ``None``.

        Returns:
            unicode:
            The filename of a new temporary file containing the original file
            contents. If the file is new, this will return ``None``.
        """
        if self.status == ReviewFileStatus.CREATED:
            return None

        contents = self.original_file_contents

        if contents is None:
            return None

        tempdir = make_tempdir()
        filename = os.path.join(tempdir, os.path.basename(self.source_file))

        with open(filename, 'wb') as fp:
            fp.write(contents)

        return filename

    def get_lines(self, first_line, num_lines=1, original=False):
        """Return the lines from the file in the given range.

        This can be used to extract lines from the original or modified file,
        as represented in the diff data. Some tool implementations can use this
        to provide more informative results (e.g., by providing suggested fixes
        to lines based on diffed/delta information coming from the program
        backing the tool).

        Args:
            first_line (int):
                The first line in the range.

            num_lines (int, optional):
                The maximum number of lines to return.

            original (bool, optional):
                Whether to return lines from the original (unmodified) file.

        Returns:
            list of unicode:
            The list of lines, up to the maximum requested. This will be
            empty if the lines could not be found.
        """
        if original:
            code_index = 2
        else:
            code_index = 5

        return list(islice(
            (
                # result[1] is the row information.
                result[1][code_index]
                for result in self._iter_lines(first_line=first_line,
                                               original=original)
            ),
            num_lines))

    def apply_patch(self, root_target_dir):
        """Apply the patch for this file to the filesystem.

        The file will be written relative to the current directory.

        Version Added:
            3.0

        Args:
            root_target_dir (unicode):
                The root directory for the project. No files are allowed to
                be created, modified, deleted, or linked to outside of this
                path.

        Raises:
            reviewbot.errors.SuspiciousFilePath:
                The patch tried to work with a file outside of
                ``root_target_dir``.
        """
        source_file = os.path.abspath(os.path.join(root_target_dir,
                                                   self.source_file))
        dest_file = os.path.abspath(os.path.join(root_target_dir,
                                                 self.dest_file))

        assert os.path.commonprefix((source_file, dest_file,
                                     root_target_dir)) == root_target_dir, (
            '%r and %r must be located within %r'
            % (source_file, dest_file, root_target_dir))

        if self.status == ReviewFileStatus.DELETED:
            try:
                os.unlink(source_file)
            except Exception as e:
                # We'll log and then continue.
                logger.warning('Unable to delete source file "%s" for '
                               'FileDiff ID=%s: %s',
                               source_file, self.id, e)
        else:
            ensure_dirs_exist(dest_file)

            if self.status == ReviewFileStatus.MOVED:
                try:
                    os.rename(source_file, dest_file)
                except Exception as e:
                    # We'll log and then continue, just creating the new file.
                    logger.warning('Unable to move source file "%s" to '
                                   'to "%s" for FileDiff ID=%s',
                                   source_file, dest_file, self.id)

            with open(dest_file, 'wb') as fp:
                fp.write(self.patched_file_contents)

        self.patched_file_path = self.dest_file

    def comment(self, text, first_line, num_lines=1, start_column=None,
                error_code=None, issue=None, rich_text=False, original=False,
                text_extra=None, severity=None):
        """Make a comment on the file.

        Version Changed:
            3.0:
            Added ``error_code``, ``severity``, ``start_column``, and
            ``text_extra`` arguments.

        Args:
            text (unicode):
                The text of the comment.

            first_line (int):
                The line number that the comment starts on. If ``None``, the
                comment is considered to be for the entire file.

            num_lines (int, optional):
                The number of lines that the comment should span.

            start_column (int, optional):
                The starting column within the code line where an error
                applied, as reported by a linter. If provided, this will be
                appended to the text.

            error_code (unicode, optional):
                An error code for the error being reported. If provided,
                this will be appended to the text.

            issue (bool, optional):
                Whether an issue should be opened.

            rich_text (bool, optional):
                Whether the comment text should be formatted using Markdown.

            original (bool, optional):
                If True, the ``first_line`` argument corresponds to the line
                number in the original file, instead of the patched file.

            severity (unicode, optional):
                A tool-specific, human-readable indication of the severity of
                this comment.

            text_extra (list of tuple, optional):
                Additional data to append to the text in ``Key: Value`` form.
                Each item is an ordered tuple of ``(Key, Value``). These will
                be placed after the default items ("Column" and "Error code").
        """
        # Some tools report a first_line of 0 to mean a 'global comment' on a
        # particular file. For now, we handle this as a special case as
        # Review Board does not currently support rendering this.
        if first_line is None or first_line <= 0:
            first_line = 1
            modified = True
        else:
            modified = (self.review.settings['comment_unmodified'] or
                        self._is_modified(first_line, num_lines))

        if modified:
            real_line = self._translate_line_num(first_line)

            if num_lines != 1:
                last_line = first_line + num_lines - 1
                real_last_line = self._translate_line_num(last_line)
                num_lines = real_last_line - real_line + 1

            if issue is None:
                issue = self.review.settings['open_issues']

            extra = []

            if start_column:
                extra.append(('Column', start_column))

            if severity:
                extra.append(('Severity', severity))

            if error_code:
                extra.append(('Error code', error_code))

            if text_extra:
                extra += text_extra

            if extra:
                text = '%s\n\n%s' % (text, '\n'.join(
                    '%s: %s' % (key, value)
                    for key, value in extra
                ))

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
            The filediff row number, or ``None`` if the line number could
            not be found.
        """
        results = self._iter_lines(original=original, first_line=line_num)

        try:
            # Return the first value (virtual line number) from the 3rd
            # entry in the tuple result (the row information).
            return next(results)[1][0]
        except StopIteration:
            return None

    def _is_modified(self, line_num, num_lines, original=False):
        """Return whether the given region is modified in the diff.

        A region is considered modified if any of the lines within are
        modified.

        Version Changed:
            3.0:
            Prior versions required the entire range to be within modified
            chunks. Now it only requires at least one of the lines to be
            modified.

        Args:
            line_num (int):
                The line number that the comment starts on.

            num_lines (int):
                The number of lines to check after line_num.

            original (bool, optional):
                If True, the ``first_line`` argument corresponds to the line
                number in the original file, instead of the patched file.

        Returns:
            bool:
            True if the region corresponds to modified code.
        """
        for chunk, row, row_line_num in self._iter_lines(first_line=line_num,
                                                         original=original):
            if (chunk['change'] != 'equal' and
                line_num <= row_line_num < line_num + num_lines):
                return True

        return False

    def _iter_lines(self, first_line=None, original=False):
        """Iterate through lines in the diff data.

        This is a convenience function for iterating through chunks in the
        diff data. This can begin iteration at a specific line number.

        Args:
            first_line (int, optional):
                A line number to begin iterating from.

            original (bool, optional):
                Whether to look for lines in the original (unmodified) file.

        Yields:
            tuple:
            A 3-tuple containing:

            1. The chunk dictionary.
            2. The list of information for the current row.
            3. The line number of the row.
        """
        # The index in a diff line of a chunk that the relevant (original vs.
        # patched) line number is stored at.
        if original:
            line_num_index = 1
        else:
            line_num_index = 4

        chunks = self.diff_data.chunks

        if first_line is not None:
            # First, we need to find the chunk with the line number. For
            # this, we'll do a simple binary search of the chunks.
            first_chunk, first_chunk_i, first_row, first_row_i = \
                self._find_line_num_info(chunks=chunks,
                                         expected_line_num=first_line,
                                         line_num_index=line_num_index)

            if first_row is None:
                # We didn't find the line, so bail.
                return

            # We found a result. Sanity-check it and then start
            # iterating.
            assert first_row[line_num_index] == first_line

            # First, iterate through the remainder of the chunk where
            # the row was found, starting at that row.
            for row in first_chunk.lines[first_row_i:]:
                yield first_chunk, row, row[line_num_index]

            # Now we'll prepare the remainder of the chunks for iteration.
            chunks = chunks[first_chunk_i + 1:]

        for chunk in chunks:
            for row in chunk['lines']:
                row_line_num = row[line_num_index]

                if row_line_num:
                    yield chunk, row, row_line_num

    def _find_line_num_info(self, chunks, expected_line_num, line_num_index):
        """Find the chunk and row for an expected line number.

        This will perform a binary search through the provided chunks, looking
        for a row that contains the expected line number. If found, the
        information on the chunk and row will be returned, allowing for
        further processing.

        Args:
            chunks (list of dict):
                The list of chunks to binary search.

            expected_line_num (int):
                The line number to look for.

            line_num_index (int):
                The index into a row containing the row's line number.

        Returns:
            tuple:
            A 4-tuple containing:

            1. The chunk containing the line number.
            2. The index of the chunk within the list of chunks.
            3. The row containing the line number.
            4. The index of the row within the chunk.

            If the line number could not be found, these will all be ``None``.
        """
        found_chunk = None
        found_chunk_i = None
        found_row = None
        found_row_i = None

        chunks = [
            (chunk_i, chunk)
            for chunk_i, chunk in enumerate(chunks)
            if chunk.lines[0][line_num_index] != ''
        ]

        low = 0
        high = len(chunks) - 1

        while low <= high:
            mid = (low + high) // 2
            chunk_i, chunk = chunks[mid]
            chunk_lines = chunk.lines
            chunk_linenum1 = chunk_lines[0][line_num_index]
            chunk_linenum2 = chunk_lines[-1][line_num_index]

            if chunk_linenum1 <= expected_line_num <= chunk_linenum2:
                # We found the chunk containing the line number. Now
                # we just need to grab the line within the chunk. That's
                # easy, since we can just index into it.
                found_chunk = chunk
                found_chunk_i = chunk_i
                found_row_i = expected_line_num - chunk_linenum1
                found_row = chunk_lines[found_row_i]
                break
            elif chunk_linenum2 < expected_line_num:
                # This chunk's lines precede the line we're looking for.
                # Narrow the search space to everything after this chunk.
                low = mid + 1
            elif chunk_linenum1 > expected_line_num:
                # This chunk's lines follow the line we're looking for.
                # Narrow the search space to everything before this chunk.
                high = mid - 1

        return found_chunk, found_chunk_i, found_row, found_row_i


class Review(object):
    """An object which orchestrates the creation of a review."""

    #: Additional text to show above the comments in the review.
    body_top = ""

    #: Additional text to show below the comments in the review.
    body_bottom = ""

    _VALID_FILEDIFF_STATUS_TYPES = {
        'copied',
        'deleted',
        'modified',
        'moved',
    }

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
        self.general_comments = []

        # Get the list of files.
        files = []

        if self.diff_revision:
            filediffs = api_root.get_files(
                review_request_id=self.review_request_id,
                diff_revision=self.diff_revision)

            for filediff in filediffs:
                # Filter out binary files and symlinks.
                if (getattr(filediff, 'binary', False) or
                    filediff.status not in self._VALID_FILEDIFF_STATUS_TYPES or
                    ('is_symlink' in filediff.extra_data and
                     filediff.extra_data['is_symlink'])):
                    continue

                files.append(File(review=self,
                                  api_filediff=filediff))

        self.files = files

    def general_comment(self, text, issue=None, rich_text=False):
        """Make a general comment.

        Args:
            text (unicode):
                The text of the comment.

            issue (bool, optional):
                Whether an issue should be opened.

            rich_text (bool, optional):
                Whether the comment text should be formatted using Markdown.
        """
        self.general_comments.append({
            'text': text,
            'issue_opened': issue or self.settings['open_issues'],
            'rich_text': rich_text,
        })

    def publish(self):
        """Upload the review to Review Board."""
        # Truncate comments to the maximum permitted amount to avoid
        # overloading the review and freezing the browser.
        max_comments = self.settings['max_comments']
        num_comments = len(self.comments) + len(self.general_comments)

        if num_comments > max_comments:
            warning = ('**Warning:** Showing %d of %d failures.'
                       % (max_comments, num_comments))

            if self.body_top:
                self.body_top = '%s\n%s' % (self.body_top, warning)
            else:
                self.body_top = warning

            if len(self.general_comments) > max_comments:
                del self.general_comments[max_comments:]
                del self.comments[:]
            else:
                del self.comments[max_comments - len(self.general_comments):]

        bot_reviews = self.api_root.get_extension(
            extension_name='reviewbotext.extension.ReviewBotExtension'
        ).get_review_bot_reviews()

        return bot_reviews.create(
            review_request_id=self.review_request_id,
            body_top=self.body_top,
            body_top_rich_text=True,
            body_bottom=self.body_bottom,
            diff_comments=json.dumps(self.comments),
            general_comments=json.dumps(self.general_comments))

    @property
    def has_comments(self):
        """Whether the review has comments."""
        return len(self.comments) + len(self.general_comments) != 0

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
