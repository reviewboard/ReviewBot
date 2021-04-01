"""Unit tests for reviewbot.tools.pyflakes."""

from __future__ import unicode_literals

import kgb
import six

from reviewbot.tools.pyflakes import PyflakesTool
from reviewbot.tools.testing import (BaseToolTestCase,
                                     ToolTestCaseMetaclass,
                                     integration_test,
                                     simulation_test)
from reviewbot.utils.process import execute


@six.add_metaclass(ToolTestCaseMetaclass)
class PyflakesToolTests(BaseToolTestCase):
    """Unit tests for reviewbot.tools.pyflakes.PyflakesTool."""

    tool_class = PyflakesTool
    tool_exe_config_key = 'pyflakes'
    tool_exe_path = '/path/to/pyflakes'

    @integration_test()
    @simulation_test(stdout=[
        "test.py:1:1 'foo' imported but unused",
        "test.py:4:5 undefined name 'func'",
        "test.py:5:1 local variable 'e' is assigned to but never used",
    ])
    def test_execute_with_lint_warnings(self):
        """Testing PyflakesTool.execute with lint warnings"""
        review, review_file = self.run_tool_execute(
            filename='test.py',
            file_contents=(
                b'import foo\n'
                b'\n'
                b'try:\n'
                b'    func()\n'
                b'except Exception as e:\n'
                b'    pass\n'
            ))

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 1,
                'num_lines': 1,
                'text': (
                    "'foo' imported but unused\n"
                    "\n"
                    "Column: 1"
                ),
                'issue_opened': True,
                'rich_text': False,
            },
            {
                'filediff_id': review_file.id,
                'first_line': 4,
                'num_lines': 1,
                'text': (
                    "undefined name 'func'\n"
                    "\n"
                    "Column: 5"
                ),
                'issue_opened': True,
                'rich_text': False,
            },
            {
                'filediff_id': review_file.id,
                'first_line': 5,
                'num_lines': 1,
                'text': (
                    "local variable 'e' is assigned to but never used\n"
                    "\n"
                    "Column: 1"
                ),
                'issue_opened': True,
                'rich_text': False,
            },
        ])

    @integration_test()
    @simulation_test(stderr=[
        'test.py:1:5: invalid syntax',
        'a = => == !!()',
        '    ^\n',
    ])
    def test_execute_with_syntax_errors(self):
        """Testing PyflakesTool.execute with syntax errors"""
        review, review_file = self.run_tool_execute(
            filename='test.py',
            file_contents=(
                b'a = => == !!()\n'
            ))

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 1,
                'num_lines': 1,
                'text': (
                    'invalid syntax\n'
                    '\n'
                    'Column: 5'
                ),
                'issue_opened': True,
                'rich_text': False,
            },
        ])

    @integration_test()
    @simulation_test(stderr=[
        'test.py: problem decoding source',
    ])
    def test_execute_with_unexpected_error(self):
        """Testing PyflakesTool.execute with unexpected errors"""
        review, review_file = self.run_tool_execute(
            filename='test.py',
            file_contents=(
                b'\00\11\22'
            ))

        self.assertEqual(review.comments, [])
        self.assertEqual(review.general_comments, [
            {
                'text': ('pyflakes could not process test.py: '
                         'problem decoding source'),
                'issue_opened': True,
                'rich_text': False,
            },
        ])

    @integration_test()
    @simulation_test()
    def test_execute_with_success(self):
        """Testing PyflakesTool.execute with no warnings or errors"""
        review, review_file = self.run_tool_execute(
            filename='test.py',
            file_contents=(
                b'print("Hello, world!")'
            ))

        self.assertEqual(review.comments, [])
        self.assertEqual(review.general_comments, [])

    def setup_simulation_test(self, stdout=[], stderr=[]):
        """Set up the simulation test for pyflakes.

        This will spy on :py:func:`~reviewbot.utils.process.execute`, making
        it return the provided stdout and stderr results.

        Args:
            stdout (list of unicode, optional):
                The outputted stdout.

            stderr (list of unicode, optional):
                The outputted stderr.
        """
        self.spy_on(execute, op=kgb.SpyOpReturn((stdout, stderr)))
