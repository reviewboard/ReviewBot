"""Common test case for Review Bot unit testing.

Version Added:
    3.0
"""

from __future__ import unicode_literals

import pprint
import re
import unittest

from rbtools.api.resource import FileDiffResource, ItemResource, RootResource
from rbtools.api.tests.base import MockTransport
from six.moves import range

from reviewbot.processing.review import File, Review


class DummyFileDiffResource(FileDiffResource):
    """A specialization of FileDiffResource that provides custom data.

    This takes in special ``_diff_data`, ``_patch``, and ``_patched_content``
    data in the payload, avoiding using HTTP requests to fetch it.
    """

    def get_patch(self, **kwargs):
        """Return the patch for this FileDiff.

        Args:
            **kwargs (unused):
                Unused keyword arguments.

        Returns:
            rbtools.api.resource.ItemResource:
            The item resource representing the patch file.
        """
        return ItemResource(
            transport=self._transport,
            payload={
                'resource': {
                    'data': self._patch,
                },
            },
            token='resource',
            url=self._url)

    def get_patched_file(self, **kwargs):
        """Return the patched version of the FileDiff's content.

        Args:
            **kwargs (unused):
                Unused keyword arguments.

        Returns:
            rbtools.api.resource.ItemResource:
            The item resource representing the patched content.
        """
        return ItemResource(
            transport=self._transport,
            payload={
                'resource': {
                    'data': self._patched_content,
                },
            },
            token='resource',
            url='%s/patched-file/' % self._url)

    def get_diff_data(self, **kwargs):
        """Return the diff data.

        Args:
            **kwargs (unused):
                Unused keyword arguments.

        Returns:
            rbtools.api.resource.ResourceDictField:
            The diff data.
        """
        return self._diff_data


class DummyRootResource(RootResource):
    """A specialization of RootResource that stubs out some functions."""

    def get_files(self, **kwargs):
        """Return all filediffs resources.

        This will always be empty.

        Args:
            **kwargs (unused):
                Unused keyword arguments.

        Returns:
            list:
            The empty list.
        """
        return []


class TestCase(unittest.TestCase):
    """Base class for Review Bot worker unit tests.

    This provides additional utility functions to aid in testing.

    Version Added:
        3.0
    """

    # Increase the maximum size allowed for showing diffs of objects.
    maxDiff = 10000

    _ws_re = re.compile(r'\s+')

    @classmethod
    def setUpClass(cls):
        super(TestCase, cls).setUpClass()

        cls.api_transport = MockTransport()
        cls.api_root = DummyRootResource(
            transport=cls.api_transport,
            payload={
                'uri_templates': {},
            },
            url='https://reviews.example.com/api/')

    @classmethod
    def tearDownClass(cls):
        super(TestCase, cls).tearDownClass()

        cls.api_transport = None

    def shortDescription(self):
        """Return the description of the current test.

        This changes the default behavior to replace all newlines with spaces,
        allowing a test description to span lines. It should still be kept
        short, though.

        Returns:
            unicode:
            The test description, without truncating lines.
        """
        doc = self._testMethodDoc

        if doc is not None:
            doc = doc.split('\n\n', 1)[0]
            doc = self._ws_re.sub(' ', doc).strip()

        return doc

    def create_review(self, review_request_id=123, diff_revision=1,
                      settings={}):
        """Create a Review for testing.

        Args:
            review_request_id (int, optional):
                The ID of the review request being reviewed.

            diff_revision (int, optional):
                The revision of the diffset being reviewed.

            settings (dict, optional):
                Custom settings to provide for the review.

        Returns:
            reviewbot.processing.review.Review:
            The resulting Review object.
        """
        return Review(
            api_root=self.api_root,
            review_request_id=review_request_id,
            diff_revision=diff_revision,
            settings=dict({
                'comment_unmodified': False,
                'open_issues': True,
            }, **settings))

    def create_review_file(self, review, filediff_id=42,
                           source_file='/test.txt',
                           dest_file='/test.txt',
                           patch=None,
                           patched_content=None,
                           diff_data=None):
        """Create a File representing a review on a filediff for testing.

        Args:
            review (reviewbot.processing.review.Review:
                The review that this File will be bound to.

            filediff_id (int, optional):
                The ID of the FileDiff being reviewed.

            source_file (unicode, optional):
                The filename of the original version of the file.

            dest_file (unicode, optional):
                The filename of the modified version of the file.

            patch (bytes, optional):
                The patch content. If not provided, one will be generated.

            patched_content (bytes, optional):
                The patched version of the file. If not provided, one will
                be generated.

            diff_data (dict, optional):
                The diff data, used to match up line numbers to diff
                virtual line numbers. If not provided, one will be generated,
                but most test suites will need to generate this themselves.

        Returns:
            reviewbot.processing.review.File:
            The resulting File object.
        """
        if patch is None:
            patch = (
                b'diff --git a/%(source_file)s b/%(dest_file)s\n'
                b'index abc123..def456 100644\n'
                b'--- a/%(source_file)s\n'
                b'+++ b/%(dest_file)s\n'
                b'@@ -2 +2 @@\n'
                b'-test\n'
                b'+test!\n'
                % {
                    b'dest_file': dest_file.encode('utf-8'),
                    b'source_file': source_file.encode('utf-8'),
                }
            )

        if patched_content is None:
            patched_content = b'test!'

        if diff_data is None:
            diff_data = self.create_diff_data(chunks=[
                {
                    'change': 'replace',
                    'lines': [
                        ('test', 'test!'),
                    ],
                }
            ])

        api_filediff = DummyFileDiffResource(
            transport=self.api_transport,
            payload={
                'id': filediff_id,
                'source_file': source_file,
                'dest_file': dest_file,
                '_diff_data': diff_data,
                '_patch': patch,
                '_patched_content': patched_content,
            },
            url=('https://reviews.example.com/api/review-requests/%s/'
                 'diffs/1/files/%s/'
                 % (review.review_request_id, filediff_id)))

        review_file = File(review=review,
                           api_filediff=api_filediff)
        review.files.append(review_file)

        return review_file

    def create_diff_data(self, chunks):
        """Create new diff data based on a simplified chunk format.

        This will generate the full diff data format based on the chunks.
        The caller needs to provide a list of chunks containing relevant
        content (any gaps will be automatically filled in).

        Args:
            chunks (list of dict):
                A simplifed list of chunk data. Each should have the
                following keys:

                ``change``:
                    One of ``equal``, ``replace``, ``insert``, or ``delete``.

                ``old_linenum``:
                    The line number of the old/original side of the chunk.

                ``new_linenum``:
                    The line number of the new/modified side of the chunk.

                ``lines``:
                    A list of lines.

                    For ``equal`` or ``replace``, each entry must be a tuple
                    of original and modified lines.

                    For ``insert`` or ``delete``, each entry must be a single
                    string for the corresponding side.

        Returns:
            dict:
            The resulting diff data.
        """
        changed_chunk_indexes = []
        new_chunks = []
        num_changes = 0
        next_old_linenum = 1
        next_new_linenum = 1
        chunk_i = 0
        line_i = 1

        for chunk in chunks:
            change = chunk.get('change', 'equal')
            chunk_old_linenum = chunk.get('old_linenum', next_old_linenum)
            chunk_new_linenum = chunk.get('new_linenum', next_new_linenum)
            lines = chunk['lines']

            if change in ('replace', 'equal'):
                skipped_lines_len = min(
                    chunk_old_linenum - next_old_linenum,
                    chunk_new_linenum - next_new_linenum)
            elif change == 'insert':
                skipped_lines_len = chunk_new_linenum - next_new_linenum
            elif change == 'delete':
                skipped_lines_len = chunk_old_linenum - next_old_linenum

            if skipped_lines_len > 0:
                new_chunks.append({
                    'change': 'equal',
                    'collapsable': False,
                    'index': chunk_i,
                    'lines': [
                        [
                            line_i + j,
                            next_old_linenum + j,
                            '',
                            '',
                            [],
                            next_new_linenum + j,
                            '',
                            '',
                            [],
                            False,
                        ]
                        for j in range(skipped_lines_len)
                    ],
                    'meta': {
                        'left_headers': [],
                        'right_headers': [],
                        'whitespace_chunk': False,
                        'whitespace_lines': [],
                    },
                    'numlines': skipped_lines_len,
                })

                chunk_i += 1
                line_i += skipped_lines_len
                next_old_linenum += skipped_lines_len
                next_new_linenum += skipped_lines_len

            if change in ('replace', 'equal'):
                new_lines = [
                    [
                        line_i + j,
                        chunk_old_linenum + j,
                        old_line,
                        [],
                        chunk_new_linenum + j,
                        new_line,
                        [],
                        False,
                    ]
                    for j, (old_line, new_line) in enumerate(lines)
                ]
            elif change == 'insert':
                new_lines = [
                    [
                        line_i + j,
                        '',
                        '',
                        [],
                        chunk_new_linenum + j,
                        new_line,
                        [],
                        False,
                    ]
                    for j, new_line in enumerate(lines)
                ]
            elif change == 'delete':
                new_lines = [
                    [
                        line_i + j,
                        chunk_old_linenum + j,
                        old_line,
                        [],
                        '',
                        '',
                        [],
                        False,
                    ]
                    for j, old_line in enumerate(lines)
                ]

            num_lines = len(new_lines)
            line_i += num_lines

            new_chunk = {
                'change': change,
                'collapsable': False,
                'index': chunk_i,
                'lines': new_lines,
                'meta': {
                    'left_headers': [],
                    'right_headers': [],
                    'whitespace_chunk': False,
                    'whitespace_lines': [],
                },
                'numlines': num_lines,
            }

            new_chunks.append(new_chunk)
            changed_chunk_indexes.append(chunk_i)

            chunk_i += 1

            if change in ('replace', 'equal'):
                next_old_linenum += num_lines
                next_new_linenum += num_lines
            elif change == 'insert':
                next_new_linenum += num_lines
            elif change == 'delete':
                next_old_linenum += num_lines

            if change != 'equal':
                num_changes += 1

        # This will help for writing unit tests, since it's hard to ensure
        # the values passed in are correct without seeing the results.
        print('Generating diff chunks...')
        pprint.pprint(new_chunks)

        return {
            'binary': False,
            'changed_chunk_indexes': changed_chunk_indexes,
            'chunks': new_chunks,
            'new_file': False,
            'num_changes': num_changes,
        }
