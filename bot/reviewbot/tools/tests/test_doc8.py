# coding: utf-8
"""Unit tests for reviewbot.tools.doc8."""

from __future__ import unicode_literals

import os

import kgb
import six

from reviewbot.tools.doc8 import Doc8Tool
from reviewbot.tools.testing import (BaseToolTestCase,
                                     ToolTestCaseMetaclass,
                                     integration_test,
                                     simulation_test)
from reviewbot.utils.filesystem import tmpdirs
from reviewbot.utils.process import execute


@six.add_metaclass(ToolTestCaseMetaclass)
class Doc8ToolTests(BaseToolTestCase):
    """Unit tests for reviewbot.tools.doc8.Doc8Tool."""

    tool_class = Doc8Tool
    tool_exe_config_key = 'doc8'
    tool_exe_path = '/path/to/doc8'

    @integration_test()
    @simulation_test(output=[
        '/path/to/test.rst:1: D000 Inline strong start-string without '
        'end-string.\n',
        '/path/to/test.rst:3: D002 Trailing whitespace\n',
    ])
    def test_execute(self):
        """Testing Doc8Tool.execute"""
        review, review_file = self.run_tool_execute(
            filename='test.rst',
            file_contents=(
                b'Here is a broken **bold*.\n'
                b'\n'
                b'And here is trailing whitespace:    \n'
            ),
            tool_settings={
                'encoding': 'utf-8',
                'max_line_length': 79,
            })

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 1,
                'num_lines': 1,
                'text': (
                    'Inline strong start-string without end-string.\n'
                    '\n'
                    'Error code: D000'
                ),
                'issue_opened': True,
                'rich_text': False,
            },
            {
                'filediff_id': review_file.id,
                'first_line': 3,
                'num_lines': 1,
                'text': (
                    'Trailing whitespace\n'
                    '\n'
                    'Error code: D002'
                ),
                'issue_opened': True,
                'rich_text': False,
            },
        ])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                '-q',
                '--max-line-length=79',
                '--file-encoding=utf-8',
                os.path.join(tmpdirs[-1], 'test.rst'),
            ],
            split_lines=True,
            ignore_errors=True)

    @integration_test()
    @simulation_test(output=[
        '/path/to/test.rst:1: D000 Inline emphasis start-string without '
        'end-string.\n',
        '/path/to/test.rst:1: D005 No newline at end of file\n',
    ])
    def test_execute_with_encoding(self):
        """Testing Doc8Tool.execute with encoding setting"""
        review, review_file = self.run_tool_execute(
            filename='test.rst',
            file_contents=(
                # This is: "*hi 🍎"
                b'\xff\xfe*\x00h\x00i\x00 \x00<\xd8N\xdf'
            ),
            tool_settings={
                'encoding': 'utf-16',
                'max_line_length': 79,
            })

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 1,
                'num_lines': 1,
                'text': (
                    'Inline emphasis start-string without end-string.\n'
                    '\n'
                    'Error code: D000'
                ),
                'issue_opened': True,
                'rich_text': False,
            },
            {
                'filediff_id': review_file.id,
                'first_line': 1,
                'num_lines': 1,
                'text': (
                    'No newline at end of file\n'
                    '\n'
                    'Error code: D005'
                ),
                'issue_opened': True,
                'rich_text': False,
            },
        ])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                '-q',
                '--max-line-length=79',
                '--file-encoding=utf-16',
                os.path.join(tmpdirs[-1], 'test.rst'),
            ],
            split_lines=True,
            ignore_errors=True)

    @integration_test()
    @simulation_test(output=[
        '/path/to/test.rst:1: D001 Line too long\n',
    ])
    def test_execute_with_max_line_length(self):
        """Testing Doc8Tool.execute with max_line_length setting"""
        review, review_file = self.run_tool_execute(
            filename='test.rst',
            file_contents=(
                b'This line will be too long.\n'
                b'\n'
                b'This will be ok.\n'
            ),
            tool_settings={
                'encoding': 'utf-8',
                'max_line_length': 20,
            })

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 1,
                'num_lines': 1,
                'text': (
                    'Line too long\n'
                    '\n'
                    'Error code: D001'
                ),
                'issue_opened': True,
                'rich_text': False,
            },
        ])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                '-q',
                '--max-line-length=20',
                '--file-encoding=utf-8',
                os.path.join(tmpdirs[-1], 'test.rst'),
            ],
            split_lines=True,
            ignore_errors=True)

    @integration_test()
    @simulation_test(output=[])
    def test_execute_with_success(self):
        """Testing Doc8Tool.execute with no errors"""
        review, review_file = self.run_tool_execute(
            filename='test.rst',
            file_contents=(
                b'Here is a **bold**.\n'
            ),
            tool_settings={
                'encoding': 'utf-8',
                'max_line_length': 79,
            })

        self.assertEqual(review.comments, [])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                '-q',
                '--max-line-length=79',
                '--file-encoding=utf-8',
                os.path.join(tmpdirs[-1], 'test.rst'),
            ],
            split_lines=True,
            ignore_errors=True)

    def setup_simulation_test(self, output=[]):
        """Set up the simulation test for pyflakes.

        This will spy on :py:func:`~reviewbot.utils.process.execute`, making
        it return the provided output.

        Args:
            output (list of unicode):
                The simulated output from the tool.
        """
        self.spy_on(execute, op=kgb.SpyOpReturn(output))
