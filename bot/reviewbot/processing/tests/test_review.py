"""Unit tests for reviewbot.processing.review.Review.

Version Added:
    3.0
"""

from __future__ import unicode_literals

import kgb

from reviewbot.testing import TestCase


class ReviewTests(kgb.SpyAgency, TestCase):
    """Unit tests for reviewbot.processing.review.Review."""

    def test_init_load_filediffs(self):
        """Testing Review.__init__ with loading FileDiffs"""
        self.spy_on(self.api_root.get_files, op=kgb.SpyOpReturn([
            self.create_filediff_resource(
                filediff_id=1,
                review_request_id=1,
                source_file='test1.txt',
                dest_file='test1.txt'),
            self.create_filediff_resource(
                filediff_id=2,
                review_request_id=1,
                source_file='test2.txt',
                dest_file='test2.txt',
                source_revision='PRE-CREATED'),
            self.create_filediff_resource(
                filediff_id=3,
                review_request_id=1,
                source_file='test3.txt',
                dest_file='test3.txt',
                status='deleted'),
            self.create_filediff_resource(
                filediff_id=4,
                review_request_id=1,
                source_file='test4.txt',
                dest_file='docs/test4.txt',
                status='moved'),
            self.create_filediff_resource(
                filediff_id=5,
                review_request_id=1,
                source_file='test5.txt',
                dest_file='docs/test5.txt',
                status='copied'),

            # These should be filtered out.
            self.create_filediff_resource(
                filediff_id=6,
                review_request_id=1,
                source_file='test6.txt',
                dest_file='test6.txt',
                status='unknown'),
            self.create_filediff_resource(
                filediff_id=7,
                review_request_id=1,
                source_file='image1.png',
                dest_file='image1.png',
                binary=True),
            self.create_filediff_resource(
                filediff_id=8,
                review_request_id=1,
                source_file='link1',
                dest_file='link1',
                extra_data={
                    'is_symlink': True,
                }),
        ]))

        review = self.create_review()

        # The symlink and image should be skipped.
        files = review.files

        self.assertEqual(len(files), 5)
        self.assertEqual(files[0].source_file, 'test1.txt')
        self.assertEqual(files[1].source_file, 'test2.txt')
        self.assertEqual(files[2].source_file, 'test3.txt')
        self.assertEqual(files[3].source_file, 'test4.txt')
        self.assertEqual(files[4].source_file, 'test5.txt')
