"""Unit tests for reviewbot.processing.review.File."""

from __future__ import unicode_literals

from reviewbot.testing import TestCase


class FileTests(TestCase):
    """Unit tests for reviewbot.processing.review.File."""

    def setUp(self):
        super(FileTests, self).setUp()

        self.review = self.create_review()
        self.review_file = self.create_review_file(
            self.review,
            diff_data=self.create_diff_data(chunks=[
                {
                    'change': 'insert',
                    'lines': [
                        'import foo',
                        'import bar',
                        'import baz',
                        'import foobarbaz',
                    ],
                    'new_linenum': 12,
                    'old_linenum': 11,
                },
                {
                    'change': 'replace',
                    'lines': [
                        ('except Exception:',
                         'except Exception as e:'),
                    ],
                    'new_linenum': 48,
                    'old_linenum': 40,
                },
            ]))

    def test_comment(self):
        """Testing File.comment"""
        self.review_file.comment('This is a comment',
                                 first_line=12)

        self.assertEqual(self.review.comments, [{
            'filediff_id': 42,
            'first_line': 12,
            'issue_opened': True,
            'num_lines': 1,
            'text': 'This is a comment',
            'rich_text': False,
        }])

    def test_comment_with_line_range(self):
        """Testing File.comment with line range"""
        self.review_file.comment('This is a comment',
                                 first_line=12,
                                 num_lines=2)

        self.assertEqual(self.review.comments, [{
            'filediff_id': 42,
            'first_line': 12,
            'issue_opened': True,
            'num_lines': 2,
            'text': 'This is a comment',
            'rich_text': False,
        }])

    def test_comment_with_first_line_0(self):
        """Testing File.comment with first_line=0"""
        self.review_file.comment('This is a comment',
                                 first_line=0)

        self.assertEqual(self.review.comments, [{
            'filediff_id': 42,
            'first_line': 1,
            'issue_opened': True,
            'num_lines': 1,
            'text': 'This is a comment',
            'rich_text': False,
        }])

    def test_comment_with_first_line_none(self):
        """Testing File.comment with first_line=0"""
        self.review_file.comment('This is a comment',
                                 first_line=None)

        self.assertEqual(self.review.comments, [{
            'filediff_id': 42,
            'first_line': 1,
            'issue_opened': True,
            'num_lines': 1,
            'text': 'This is a comment',
            'rich_text': False,
        }])

    def test_comment_with_unmodified_line_range(self):
        """Testing File.comment on unmodified line range"""
        self.review_file.comment('This is a comment',
                                 first_line=1,
                                 num_lines=2)

        self.assertEqual(self.review.comments, [])

    def test_comment_with_unmodified_line_range_with_comment_unmodified(self):
        """Testing File.comment on unmodified line range with
        comment_unmodified=True
        """
        self.review.settings['comment_unmodified'] = True
        self.review_file.comment('This is a comment',
                                 first_line=1,
                                 num_lines=2)

        self.assertEqual(self.review.comments, [{
            'filediff_id': 42,
            'first_line': 1,
            'issue_opened': True,
            'num_lines': 2,
            'text': 'This is a comment',
            'rich_text': False,
        }])

    def test_comment_with_issue_true(self):
        """Testing File.comment with issue=False"""
        self.review_file.comment('This is a comment',
                                 first_line=12,
                                 issue=True)

        self.assertEqual(self.review.comments, [{
            'filediff_id': 42,
            'first_line': 12,
            'issue_opened': True,
            'num_lines': 1,
            'text': 'This is a comment',
            'rich_text': False,
        }])

    def test_comment_with_issue_false(self):
        """Testing File.comment with issue=False"""
        self.review_file.comment('This is a comment',
                                 first_line=12,
                                 issue=False)

        self.assertEqual(self.review.comments, [{
            'filediff_id': 42,
            'first_line': 12,
            'issue_opened': False,
            'num_lines': 1,
            'text': 'This is a comment',
            'rich_text': False,
        }])

    def test_comment_with_issue_none_and_setting_true(self):
        """Testing File.comment with issue=None and
        settings['open_issues']=True
        """
        self.review.settings['open_issues'] = True
        self.review_file.comment('This is a comment',
                                 first_line=12)

        self.assertEqual(self.review.comments, [{
            'filediff_id': 42,
            'first_line': 12,
            'issue_opened': True,
            'num_lines': 1,
            'text': 'This is a comment',
            'rich_text': False,
        }])

    def test_comment_with_issue_none_and_setting_false(self):
        """Testing File.comment with issue=None and
        settings['open_issues']=False
        """
        self.review.settings['open_issues'] = False
        self.review_file.comment('This is a comment',
                                 first_line=12)

        self.assertEqual(self.review.comments, [{
            'filediff_id': 42,
            'first_line': 12,
            'issue_opened': False,
            'num_lines': 1,
            'text': 'This is a comment',
            'rich_text': False,
        }])

    def test_comment_with_rich_text_true(self):
        """Testing File.comment with rich_text=True"""
        self.review_file.comment('This is a comment',
                                 first_line=12,
                                 rich_text=True)

        self.assertEqual(self.review.comments, [{
            'filediff_id': 42,
            'first_line': 12,
            'issue_opened': True,
            'num_lines': 1,
            'text': 'This is a comment',
            'rich_text': True,
        }])

    def test_comment_with_start_column(self):
        """Testing File.comment with start_column"""
        self.review_file.comment('This is a comment',
                                 first_line=12,
                                 start_column=10)

        self.assertEqual(self.review.comments, [{
            'filediff_id': 42,
            'first_line': 12,
            'issue_opened': True,
            'num_lines': 1,
            'text': (
                'This is a comment\n'
                '\n'
                'Column: 10'
            ),
            'rich_text': False,
        }])

    def test_comment_with_error_code(self):
        """Testing File.comment with error_code"""
        self.review_file.comment('This is a comment',
                                 first_line=12,
                                 error_code='W123')

        self.assertEqual(self.review.comments, [{
            'filediff_id': 42,
            'first_line': 12,
            'issue_opened': True,
            'num_lines': 1,
            'text': (
                'This is a comment\n'
                '\n'
                'Error code: W123'
            ),
            'rich_text': False,
        }])

    def test_comment_with_start_column_and_error_code(self):
        """Testing File.comment with start_column and error_code"""
        self.review_file.comment('This is a comment',
                                 first_line=12,
                                 start_column=10,
                                 error_code='W123')

        self.assertEqual(self.review.comments, [{
            'filediff_id': 42,
            'first_line': 12,
            'issue_opened': True,
            'num_lines': 1,
            'text': (
                'This is a comment\n'
                '\n'
                'Column: 10\n'
                'Error code: W123'
            ),
            'rich_text': False,
        }])
