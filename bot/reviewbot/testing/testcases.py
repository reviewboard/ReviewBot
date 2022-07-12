"""Common test case for Review Bot unit testing.

Version Added:
    3.0
"""

from __future__ import unicode_literals

import os
import pprint
import re
from contextlib import contextmanager
from copy import deepcopy

try:
    # Python 2
    import unittest2 as unittest
except ImportError:
    # Python 3
    import unittest

import six
from rbtools.api.resource import (FileAttachmentListResource,
                                  FileDiffResource,
                                  ItemResource,
                                  ListResource,
                                  RootResource)
from rbtools.api.tests.base import MockTransport
from six.moves import range

from reviewbot.config import config, reset_config
from reviewbot.processing.review import File, Review


_UNSET = object()


class FileAttachmentItemResource(ItemResource):
    """An item resource for file attachments.

    This exists so we can more easily spy on methods for this resource.
    """


class FileAttachmentListResource(FileAttachmentListResource):
    """A list resource for file attachments.

    This stubs out some functionality for testing purposes.
    """

    def upload_attachment(self, **kwargs):
        """Upload a file attachment.

        This will construct a :py:meth:`FileAttachmentItemResource` that can
        be spied on.

        Args:
            **kwargs (dict, unused):
                Unused keyword arguments.

        Returns:
            FileAttachmentItemResource:
            The resulting item resource.
        """
        return FileAttachmentItemResource(
            transport=self._transport,
            payload={
                'user_file_attachment': {
                    'id': 123,
                    'absolute_url': '/path/to/attachment.txt',
                },
            },
            token='user_file_attachment',
            url='%s/123/' % self._url)


class DummyFileDiffResource(FileDiffResource):
    """A specialization of FileDiffResource that provides custom data.

    This takes in special ``_diff_data`, ``_patch``, ``_original_content``,
    and ``_patched_content`` data in the payload, avoiding using HTTP requests
    to fetch it.
    """

    def __getattribute__(self, name):
        """Return an attribute from the resource.

        This will conditionally allow access to ``get_original_file()`` and
        ``get_patched_file()`` methods based on whether original/patched
        file content is set.

        Args:
            name (str):
                The name of the attribute.

        Returns:
            object:
            The attribute value.

        Raises:
            AttributeError:
                The requested attribute does not exist.
        """
        if name == 'get_original_file':
            if self._original_content is not None:
                return self._get_original_file
        elif name == 'get_patched_file':
            if self._patched_content is not None:
                return self._get_patched_file

        return super(DummyFileDiffResource, self).__getattribute__(name)

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

    def _get_original_file(self, **kwargs):
        """Return the original version of the FileDiff's content.

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
                    'data': self._original_content,
                },
            },
            token='resource',
            url='%s/original-file/' % self._url)

    def _get_patched_file(self, **kwargs):
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


class RepositoryListResource(ListResource):
    """An list resource for repositories.

    This exists so we can more easily spy on methods for this resource.

    Version Added:
        3.0
    """

    def __init__(self, **kwargs):
        super(RepositoryListResource, self).__init__(
            token='repositories',
            **kwargs)


class ReviewBotReviewResource(ItemResource):
    """An item resource for Review Bot reviews.

    This exists so we can more easily spy on methods for this resource.
    """


class ReviewBotReviewsResource(ListResource):
    """A list resource for Review Bot reviews.

    This stubs out some functionality for testing purposes.
    """

    def create(self, **kwargs):
        """Create a new item resource.

        This will construct a :py:meth:`ReviewBotReviewResource` that can be
        spied on.

        Args:
            **kwargs (dict, unused):
                Unused keyword arguments.

        Returns:
            ReviewBotReviewResource:
            The resulting item resource.
        """
        return ReviewBotReviewResource(
            transport=self._transport,
            payload={
                'review_bot_review': {
                    'id': 123,
                }
            },
            token='review_bot_review',
            url='%s123/' % self._url)


class ReviewBotToolsResource(ListResource):
    """A list resource for Review Bot reviews.

    This stubs out some functionality for testing purposes.
    """

    def create(self, **kwargs):
        """Create a new item resource.

        This will actually construct nothing at all. It's intended to be
        spied on.

        Args:
            **kwargs (dict, unused):
                Unused keyword arguments.

        Returns:
            object:
            ``None``, always.
        """
        return None


class ReviewBotExtensionResource(ItemResource):
    """An item resource for the Review Bot extension.

    This stubs out some functionality for testing purposes.
    """

    def get_review_bot_reviews(self, **kwargs):
        """Return a new Review Bot reviews list resource.

        Args:
            **kwargs (dict, unused):
                Unused keyword arguments.

        Returns:
            ReviewBotReviewResource:
            The new list resource.
        """
        return ReviewBotReviewsResource(
            transport=self._transport,
            payload={
                'total_results': 0,
            },
            url='%sreview-bot-reviews/' % self._url)

    def get_tools(self, **kwargs):
        """Return a new Review Bot tools list resource.

        Args:
            **kwargs (dict, unused):
                Unused keyword arguments.

        Returns:
            ReviewBotToolsResource:
            The new list resource.
        """
        return ReviewBotToolsResource(
            transport=self._transport,
            payload={
                'total_results': 0,
            },
            url='%stools/' % self._url)


class StatusUpdateResource(ItemResource):
    """An item resource for status updates.

    This stubs out some functionality for testing purposes.
    """

    def update(self, **kwargs):
        """Update the item resource.

        This does nothing. It's intended to be spied on.

        Args:
            **kwargs (dict, unused):
                Unused keyword arguments.
        """
        pass


class DummyRootResource(RootResource):
    """A specialization of RootResource that stubs out some functions."""

    def get_extension(self, extension_name, **kwargs):
        """Return an extension resource.

        This only supports the Review Bot extension ID.

        Args:
            extension_name (unicode):
                The extension name requested.

            **kwargs (dict):
                Unused keyword arguments.

        Returns:
            ReviewBotExtensionResource:
            The extension resource instance.
        """
        assert extension_name == 'reviewbotext.extension.ReviewBotExtension'

        return ReviewBotExtensionResource(
            transport=self._transport,
            payload={},
            url='%sextensions/%s/' % (self._url, extension_name))

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

    def get_repositories(self, **kwargs):
        """Return all repository resources.

        This will be empty by default. Consumers can spy on this to override
        results.

        Args:
            **kwargs (unused):
                Unused keyword arguments.

        Returns:
            RepositoryListResource:
            The resulting repository list resource.
        """
        return RepositoryListResource(
            transport=self._transport,
            payload={
                'total_results': 0,
            },
            url='%srepositories/' % self._url)

    def get_status_update(self, review_request_id, status_update_id,
                          **kwargs):
        """Return a status update item resource.

        Args:
            review_request_id (int):
                The ID of the review request.

            status_update_id (Int):
                The ID of the status update.

            **kwargs (dict, unused):
                Additional keyword arguments.

        Returns:
            StatusUpdateResource:
            The resulting status update resource.
        """
        return StatusUpdateResource(
            transport=self._transport,
            payload={
                'status_update': {
                    'id': status_update_id,
                },
            },
            url=('%sreview-requests/%s/status-updates/%s/'
                 % (self._url, review_request_id, status_update_id)))

    def get_user_file_attachments(self, username, **kwargs):
        """Return a user file attachment list resource.

        Args:
            username (unicode):
                The username for the user who owns the file attachments.

            **kwargs (dict, unused):
                Additional keyword arguments.

        Returns:
            FileAttachmentListResource:
            The resulting user file attachment list resource.
        """
        return FileAttachmentListResource(
            transport=self._transport,
            payload={
                'total_results': 0,
            },
            url='%susers/%s/user-file-attachments/' % (self._url, username))


class TestCase(unittest.TestCase):
    """Base class for Review Bot worker unit tests.

    This provides additional utility functions to aid in testing.

    Version Added:
        3.0
    """

    #: Whether to preserve the PATH environment variable.
    #:
    #: Type:
    #:     bool
    preserve_path_env = False

    #: Custom configuration used for all tests.
    #:
    #: This will be applied when setting up the test.
    #:
    #: Type:
    #:     dict
    config = {}

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

        # Stub out the PATH environment variable by default, so that we don't
        # have tests dependent on what's installed locally.
        cls._old_path = os.environ['PATH']

        if not cls.preserve_path_env:
            os.environ['PATH'] = ''

    @classmethod
    def tearDownClass(cls):
        super(TestCase, cls).tearDownClass()

        cls.api_transport = None
        os.environ['PATH'] = cls._old_path

    def setUp(self):
        super(TestCase, self).setUp()

        # Reset the configuration back to defaults, so tests don't impact
        # each other, and load any custom configuration.
        reset_config()
        config.update(self.config)

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

    @contextmanager
    def override_config(self, new_config):
        """Override the Review Bot configuration temporarily.

        This context manager allows a caller to set brand-new configuration
        for the duration of the context.

        Args:
            new_config (dict):
                The new configuration. This will be merged into a copy of the
                default configuration.

        Context:
            Code will be executed with the new configuration.
        """
        old_config = deepcopy(config)

        reset_config()

        # We'll attempt a very simple sort of merge, since at the time of this
        # implementation, we have a very simple default config schema.
        for key, value in six.iteritems(new_config):
            if isinstance(value, dict):
                config[key].update(value)
            else:
                config[key] = value

        try:
            yield
        finally:
            config.clear()
            config.update(old_config)

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
                           source_revision='abc123',
                           status='modified',
                           patch=None,
                           original_content=_UNSET,
                           patched_content=_UNSET,
                           patched_file_path=None,
                           diff_data=None,
                           extra_data={}):
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

            source_revision (unicode, optional):
                The source revision for the file.

            status (unicode, optional):
                The status value set for the FileDiff.

            patch (bytes, optional):
                The patch content. If not provided, one will be generated.

            original_content (bytes, optional):
                The original version of the file. If not provided, one will
                be generated.

            patched_content (bytes, optional):
                The patched version of the file. If not provided, one will
                be generated.

            patched_file_path (unicode, optional):
                The local path to the patched file content.

            diff_data (dict, optional):
                The diff data, used to match up line numbers to diff
                virtual line numbers. If not provided, one will be generated,
                but most test suites will need to generate this themselves.

            extra_data (dict, optional):
                Extra data to attach in the FileDiff.

        Returns:
            reviewbot.processing.review.File:
            The resulting File object.
        """
        api_filediff = self.create_filediff_resource(
            filediff_id=filediff_id,
            review_request_id=review.review_request_id,
            source_file=source_file,
            dest_file=dest_file,
            source_revision=source_revision,
            status=status,
            patch=patch,
            original_content=original_content,
            patched_content=patched_content,
            diff_data=diff_data,
            extra_data=extra_data)

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
                            '==',
                            [],
                            next_new_linenum + j,
                            '==',
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

    def create_filediff_resource(self, filediff_id=42,
                                 review_request_id=123,
                                 source_file='/test.txt',
                                 source_revision='abc123',
                                 dest_file='/test.txt',
                                 status='modified',
                                 binary=False,
                                 patch=None,
                                 original_content=_UNSET,
                                 patched_content=_UNSET,
                                 diff_data=None,
                                 extra_data={}):
        """Create a FileDiffResource for testing.

        Args:
            filediff_id (int, optional):
                The ID of the FileDiff being reviewed.

            review_request_id (int, optional):
                The ID of the review request that owns the FileDiff.

            source_file (unicode, optional):
                The filename of the original version of the file.

            source_revision (unicode, optional):
                The source revision for the file.

            dest_file (unicode, optional):
                The filename of the modified version of the file.

            status (unicode, optional):
                The status value set for the FileDiff.

            binary (bool, optional):
                Whether this is a binary file.

            patch (bytes, optional):
                The patch content. If not provided, one will be generated.

            original_content (bytes, optional):
                The original version of the file. If not provided, one will
                be generated.

            patched_content (bytes, optional):
                The patched version of the file. If not provided, one will
                be generated.

            diff_data (dict, optional):
                The diff data, used to match up line numbers to diff
                virtual line numbers. If not provided, one will be generated,
                but most test suites will need to generate this themselves.

            extra_data (dict, optional):
                Extra data to attach in the FileDiff.

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

        if original_content is _UNSET:
            original_content = b'original file!'

        if patched_content is _UNSET:
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

        return DummyFileDiffResource(
            transport=self.api_transport,
            payload={
                'id': filediff_id,
                'source_file': source_file,
                'source_revision': source_revision,
                'dest_file': dest_file,
                'status': status,
                'binary': binary,
                'extra_data': extra_data,
                '_diff_data': diff_data,
                '_patch': patch,
                '_original_content': original_content,
                '_patched_content': patched_content,
            },
            url=('https://reviews.example.com/api/review-requests/%s/'
                 'diffs/1/files/%s/'
                 % (review_request_id, filediff_id)))
