"""Unit tests for reviewbot.tools.gofmt."""

from __future__ import unicode_literals

import os

import kgb
import six

from reviewbot.tools.gofmt import GofmtTool
from reviewbot.tools.testing import (BaseToolTestCase,
                                     ToolTestCaseMetaclass,
                                     integration_test,
                                     simulation_test)
from reviewbot.utils.filesystem import tmpdirs
from reviewbot.utils.process import execute


@six.add_metaclass(ToolTestCaseMetaclass)
class GofmtToolTests(BaseToolTestCase):
    """Unit tests for reviewbot.tools.gofmt.GofmtTool."""

    tool_class = GofmtTool
    tool_exe_config_key = 'go'
    tool_exe_path = '/path/to/go'

    @integration_test()
    @simulation_test(stdout='test.go')
    def test_execute(self):
        """Testing GofmtTool.execute"""
        review, review_file = self.run_tool_execute(
            filename='test.go',
            file_contents=(
                b'package foo\n'
                b'\n'
                b'func foo() {\n'
                b' return;\n'
                b'}\n'
            ))

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 1,
                'num_lines': 1,
                'text': (
                    'This file contains formatting errors and should be run '
                    'through `go fmt`.'
                ),
                'issue_opened': True,
                'rich_text': True,
            },
        ])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                'fmt',
                os.path.join(tmpdirs[-1], 'test.go'),
            ],
            ignore_errors=True,
            return_errors=True)

    @integration_test()
    @simulation_test(stderr=(
        "can't load package: package main:\n"
        "/path/to/test.go:1:1: expected 'package', found 'func'\n"
    ))
    def test_execute_with_parse_error(self):
        """Testing GofmtTool.execute with .go parse error"""
        review, review_file = self.run_tool_execute(
            filename='test.go',
            file_contents=(
                b'func foo() {}\n'
            ))

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 1,
                'num_lines': 1,
                'text': (
                    "expected 'package', found 'func'\n"
                    "\n"
                    "Column: 1"
                ),
                'issue_opened': True,
                'rich_text': False,
            },
        ])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                'fmt',
                os.path.join(tmpdirs[-1], 'test.go'),
            ],
            ignore_errors=True,
            return_errors=True)

    @integration_test()
    @simulation_test()
    def test_execute_with_success(self):
        """Testing GofmtTool.execute with no errors"""
        review, review_file = self.run_tool_execute(
            filename='test.go',
            file_contents=(
                b'package foo\n'
                b'\n'
                b'func foo() {\n'
                b'\treturn\n'
                b'}\n'
            ))

        self.assertEqual(review.comments, [])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                'fmt',
                os.path.join(tmpdirs[-1], 'test.go'),
            ],
            ignore_errors=True,
            return_errors=True)

    def setup_simulation_test(self, stdout='', stderr=''):
        """Set up the simulation test for go fmt.

        This will spy on :py:func:`~reviewbot.utils.process.execute`, making
        it return the provided stdout and stderr results.

        Args:
            stdout (unicode, optional):
                The outputted stdout.

            stderr (unicode, optional):
                The outputted stderr.
        """
        self.spy_on(execute, op=kgb.SpyOpReturn((stdout, stderr)))
