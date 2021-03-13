"""Unit tests for reviewbot.tools.pyflakes."""

from __future__ import unicode_literals

import kgb

from reviewbot.testing import TestCase
from reviewbot.tools.pyflakes import PyflakesTool
from reviewbot.utils.process import execute


class PyflakesToolTests(kgb.SpyAgency, TestCase):
    """Unit tests for reviewbot.tools.pyflakes.PyflakesTool."""

    def test_handle_file_with_lint_warnings(self):
        """Testing PyflakesTool.handle_file with lint warnings"""
        self.spy_on(execute, op=kgb.SpyOpReturn((
            [
                "test.py:12:0: 'foo' imported but unused",
                "test.py:48:8: local variable 'e' is asigned to but never "
                "used",
            ],
            [],
        )))

        review = self.create_review()
        review_file = self.create_review_file(
            review,
            source_file='test.py',
            dest_file='test.py',
            diff_data=self.create_diff_data(chunks=[
                {
                    'change': 'insert',
                    'lines': ['import foo'],
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

        tool = PyflakesTool()
        tool.handle_file(review_file)

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 12,
                'num_lines': 1,
                'text': "'foo' imported but unused",
                'issue_opened': True,
                'rich_text': False,
            },
            {
                'filediff_id': review_file.id,
                'first_line': 41,
                'num_lines': 1,
                'text': "local variable 'e' is asigned to but never used",
                'issue_opened': True,
                'rich_text': False,
            },
        ])

    def test_handle_file_with_syntax_errors(self):
        """Testing PyflakesTool.handle_file with syntax errors"""
        self.spy_on(execute, op=kgb.SpyOpReturn((
            [],
            [
                'test.py:1:5: invalid syntax',
                'a = => == !!()',
                '    ^',
                'test.py:15: no offset line this time',
                '---+++---',
            ],
        )))

        review = self.create_review()
        review_file = self.create_review_file(
            review,
            source_file='test.py',
            dest_file='test.py',
            diff_data=self.create_diff_data(chunks=[
                {
                    'change': 'insert',
                    'lines': ['a = => == !!()'],
                    'new_linenum': 1,
                    'old_linenum': 0,
                },
                {
                    'change': 'insert',
                    'lines': ['---+++---\n'],
                    'new_linenum': 15,
                    'old_linenum': 13,
                },
            ]))

        tool = PyflakesTool()
        tool.handle_file(review_file)

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 1,
                'num_lines': 1,
                'text': 'invalid syntax',
                'issue_opened': True,
                'rich_text': False,
            },
            {
                'filediff_id': review_file.id,
                'first_line': 15,
                'num_lines': 1,
                'text': 'no offset line this time',
                'issue_opened': True,
                'rich_text': False,
            },
        ])

    def test_handle_file_with_unexpected_error(self):
        """Testing PyflakesTool.handle_file with unexpected errors"""
        self.spy_on(execute, op=kgb.SpyOpReturn((
            [],
            [
                'test.py: something went horribly wrong',
                'test.py: and again!',
            ],
        )))

        review = self.create_review()
        review_file = self.create_review_file(
            review,
            source_file='test.py',
            dest_file='test.py',
            diff_data=self.create_diff_data(chunks=[
                {
                    'change': 'insert',
                    'lines': ['a = => == !!()'],
                    'new_linenum': 1,
                    'old_linenum': 0,
                },
                {
                    'change': 'insert',
                    'lines': ['---+++---\n'],
                    'new_linenum': 15,
                    'old_linenum': 13,
                },
            ]))

        tool = PyflakesTool()
        tool.handle_file(review_file)

        self.assertEqual(review.comments, [])
        self.assertEqual(review.general_comments, [
            {
                'text': ('pyflakes could not process test.py: '
                         'something went horribly wrong'),
                'issue_opened': True,
                'rich_text': False,
            },
            {
                'text': 'pyflakes could not process test.py: and again!',
                'issue_opened': True,
                'rich_text': False,
            },
        ])

    def test_handle_file_with_success(self):
        """Testing PyflakesTool.handle_file with no warnings or errors"""
        self.spy_on(execute, op=kgb.SpyOpReturn(([], [])))

        review = self.create_review()
        review_file = self.create_review_file(
            review,
            source_file='test.py',
            dest_file='test.py')

        tool = PyflakesTool()
        tool.handle_file(review_file)

        self.assertEqual(review.comments, [])
        self.assertEqual(review.general_comments, [])
