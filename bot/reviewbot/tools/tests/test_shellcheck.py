"""Unit tests for reviewbot.tools.shellcheck."""

from __future__ import unicode_literals

import json
import os

import kgb
import six

from reviewbot.tools.shellcheck import ShellCheckTool
from reviewbot.tools.testing import (BaseToolTestCase,
                                     ToolTestCaseMetaclass,
                                     integration_test,
                                     simulation_test)
from reviewbot.utils.filesystem import tmpdirs
from reviewbot.utils.process import execute


@six.add_metaclass(ToolTestCaseMetaclass)
class ShellCheckToolTests(BaseToolTestCase):
    """Unit tests for reviewbot.tools.shellcheck.ShellCheckTool."""

    tool_class = ShellCheckTool
    tool_exe_config_key = 'shellcheck'
    tool_exe_path = '/path/to/shellcheck'

    SAMPLE_BASH_CODE = (
        b'#!/bin/bash\n'
        b'\n'
        b'eval `foo`\n'
        b'\n'
        b'run-thing --param=$VALUE\n'
    )

    def test_get_can_handle_file_with_file_extensions(self):
        """Testing ShellCheckTool.get_can_handle_file with file extensions"""
        for filename in ('test.bash',
                         'test.dash',
                         'test.ksh',
                         'test.sh'):
            self.assertTrue(
                self.run_get_can_handle_file(filename=filename),
                'Expected get_can_handle_file() to return True for "%s", but '
                'it returned False.'
                % filename)

        self.assertFalse(self.run_get_can_handle_file(filename='test.txt'))

    def test_get_can_handle_file_with_shebangs(self):
        """Testing ShellCheckTool.get_can_handle_file with shebangs"""
        for shebang in ('#!/bin/bash',
                        '#!/bin/dash',
                        '#!/bin/ksh',
                        '#!/bin/sh',
                        '#!/usr/bin/bash',
                        '#!/usr/bin/dash',
                        '#!/usr/bin/ksh',
                        '#!/usr/bin/sh',
                        '#!/usr/local/bin/bash',
                        '#!/usr/local/bin/dash',
                        '#!/usr/local/bin/ksh',
                        '#!/usr/local/bin/sh',
                        '#!/usr/bin/env bash',
                        '#!/usr/bin/env dash',
                        '#!/usr/bin/env ksh',
                        '#!/usr/bin/env sh',
                        '#!/bin/sh -e',
                        '#!/usr/bin/env bash --posix'):
            self.assertTrue(
                self.run_get_can_handle_file(
                    filename='test.txt',
                    file_contents=('%s\n' % shebang).encode('utf-8')),
                'Expected get_can_handle_file() to return True for "%s", but '
                'it returned False.'
                % shebang)

        self.assertFalse(self.run_get_can_handle_file(
            filename='test.txt',
            file_contents=b'#!/usr/bin/perl\n'))

    @integration_test()
    @simulation_test(output_payload={
        'comments': [
            {
                'code': 2046,
                'column': 6,
                'endColumn': 19,
                'endLine': 3,
                'file': '/test.sh',
                'fix': None,
                'level': 'warning',
                'line': 3,
                'message': 'Quote this to prevent word splitting.',
            },
            {
                'code': 2006,
                'column': 6,
                'endColumn': 11,
                'endLine': 3,
                'file': '/test.sh',
                'fix': {
                    'replacements': [
                        {
                            'column': 6,
                            'endColumn': 7,
                            'endLine': 3,
                            'insertionPoint': 'afterEnd',
                            'line': 3,
                            'precedence': 7,
                            'replacement': '$(',
                        },
                        {
                            'column': 10,
                            'endColumn': 11,
                            'endLine': 3,
                            'insertionPoint': 'beforeStart',
                            'line': 3,
                            'precedence': 7,
                            'replacement': ')',
                        },
                    ],
                },
                'level': 'style',
                'line': 3,
                'message': ('Use $(...) notation instead of legacy '
                            'backticks `...`.'),
            },
            {
                'code': 2086,
                'column': 19,
                'endColumn': 25,
                'endLine': 5,
                'file': '/test.sh',
                'fix': {
                    'replacements': [
                        {
                            'column': 19,
                            'endColumn': 19,
                            'endLine': 5,
                            'insertionPoint': 'afterEnd',
                            'line': 5,
                            'precedence': 7,
                            'replacement': '"',
                        },
                        {
                            'column': 25,
                            'endColumn': 25,
                            'endLine': 5,
                            'insertionPoint': 'beforeStart',
                            'line': 5,
                            'precedence': 7,
                            'replacement': '"',
                        },
                    ],
                },
                'level': 'info',
                'line': 5,
                'message': ('Double quote to prevent globbing and word '
                            'splitting.'),
            },
        ],
    })
    def test_execute(self):
        """Testing ShellCheckTool.execute"""
        review, review_file = self.run_tool_execute(
            filename='test.sh',
            file_contents=self.SAMPLE_BASH_CODE,
            tool_settings={
                'severity': 'style',
            })

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 3,
                'num_lines': 1,
                'text': (
                    'Quote this to prevent word splitting.\n'
                    '\n'
                    'Column: 6\n'
                    'Severity: warning\n'
                    'Error code: 2046'
                ),
                'issue_opened': True,
                'rich_text': True,
            },
            {
                'filediff_id': review_file.id,
                'first_line': 3,
                'num_lines': 1,
                'text': (
                    'Use $(...) notation instead of legacy backticks `...`.\n'
                    '\n'
                    'Suggested replacement:\n'
                    '```eval $(foo)```\n'
                    '\n'
                    'Column: 6\n'
                    'Severity: style\n'
                    'Error code: 2006'
                ),
                'issue_opened': True,
                'rich_text': True,
            },
            {
                'filediff_id': review_file.id,
                'first_line': 5,
                'num_lines': 1,
                'text': (
                    'Double quote to prevent globbing and word splitting.\n'
                    '\n'
                    'Suggested replacement:\n'
                    '```run-thing --param="$VALUE"```\n'
                    '\n'
                    'Column: 19\n'
                    'Severity: info\n'
                    'Error code: 2086'
                ),
                'issue_opened': True,
                'rich_text': True,
            },
        ])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                '--color=never',
                '--format=json1',
                '--severity=style',
                os.path.join(tmpdirs[-1], 'test.sh'),
            ],
            ignore_errors=True)

    @integration_test()
    @simulation_test(output_payload={
        'comments': [
            {
                'code': 2046,
                'column': 6,
                'endColumn': 19,
                'endLine': 3,
                'file': '/test.sh',
                'fix': None,
                'level': 'warning',
                'line': 3,
                'message': 'Quote this to prevent word splitting.',
            },
        ],
    })
    def test_execute_with_severity(self):
        """Testing ShellCheckTool.execute with severity setting"""
        review, review_file = self.run_tool_execute(
            filename='test.sh',
            file_contents=self.SAMPLE_BASH_CODE,
            tool_settings={
                'severity': 'warning',
            })

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 3,
                'num_lines': 1,
                'text': (
                    'Quote this to prevent word splitting.\n'
                    '\n'
                    'Column: 6\n'
                    'Severity: warning\n'
                    'Error code: 2046'
                ),
                'issue_opened': True,
                'rich_text': True,
            },
        ])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                '--color=never',
                '--format=json1',
                '--severity=warning',
                os.path.join(tmpdirs[-1], 'test.sh'),
            ],
            ignore_errors=True)

    @integration_test()
    @simulation_test(output_payload={
        'comments': [
            {
                'code': 2006,
                'column': 6,
                'endColumn': 11,
                'endLine': 3,
                'file': '/test.sh',
                'fix': {
                    'replacements': [
                        {
                            'column': 6,
                            'endColumn': 7,
                            'endLine': 3,
                            'insertionPoint': 'afterEnd',
                            'line': 3,
                            'precedence': 7,
                            'replacement': '$(',
                        },
                        {
                            'column': 10,
                            'endColumn': 11,
                            'endLine': 3,
                            'insertionPoint': 'beforeStart',
                            'line': 3,
                            'precedence': 7,
                            'replacement': ')',
                        },
                    ],
                },
                'level': 'style',
                'line': 3,
                'message': ('Use $(...) notation instead of legacy '
                            'backticks `...`.'),
            },
        ],
    })
    def test_execute_with_exclude(self):
        """Testing ShellCheckTool.execute with exclude setting"""
        review, review_file = self.run_tool_execute(
            filename='test.sh',
            file_contents=self.SAMPLE_BASH_CODE,
            tool_settings={
                'severity': 'style',
                'exclude': '2046, 2086',
            })

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 3,
                'num_lines': 1,
                'text': (
                    'Use $(...) notation instead of legacy backticks `...`.\n'
                    '\n'
                    'Suggested replacement:\n'
                    '```eval $(foo)```\n'
                    '\n'
                    'Column: 6\n'
                    'Severity: style\n'
                    'Error code: 2006'
                ),
                'issue_opened': True,
                'rich_text': True,
            },
        ])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                '--color=never',
                '--format=json1',
                '--severity=style',
                '--exclude=2046,2086',
                os.path.join(tmpdirs[-1], 'test.sh'),
            ],
            ignore_errors=True)

    @integration_test()
    @simulation_test(output_payload={
        'comments': [
            {
                'code': 1089,
                'column': 1,
                'endColumn': 1,
                'endLine': 3,
                'file': '/test.sh',
                'fix': None,
                'level': 'error',
                'line': 3,
                'message': ('Parsing stopped here. Is this keyword correctly '
                            'matched up?'),
            },
        ],
    })
    def test_execute_with_syntax_error(self):
        """Testing ShellCheckTool.execute with syntax error in file"""
        review, review_file = self.run_tool_execute(
            filename='test.sh',
            file_contents=(
                b'#!/bin/bash\n'
                b'\n'
                b'}])\n'
            ),
            tool_settings={
                'severity': 'style',
            })

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 3,
                'num_lines': 1,
                'text': (
                    'Parsing stopped here. Is this keyword correctly matched '
                    'up?\n'
                    '\n'
                    'Column: 1\n'
                    'Severity: error\n'
                    'Error code: 1089'
                ),
                'issue_opened': True,
                'rich_text': True,
            },
        ])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                '--color=never',
                '--format=json1',
                '--severity=style',
                os.path.join(tmpdirs[-1], 'test.sh'),
            ],
            ignore_errors=True)

    @integration_test()
    @simulation_test(output_payload=(
        'Unknown value for --severity. Valid options are: error, warning, '
        'info, style'
    ))
    def test_execute_with_bad_exclude_setting(self):
        """Testing ShellCheckTool.execute with bad exclude setting"""
        review, review_file = self.run_tool_execute(
            filename='test.sh',
            file_contents=self.SAMPLE_BASH_CODE,
            tool_settings={
                'severity': 'xxx',
            })

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 1,
                'num_lines': 1,
                'text': (
                    'The shellcheck returned an unexpected result. Check '
                    'to make sure that your configured settings in Review '
                    'Bot are correct.\n'
                    '\n'
                    'Error message:\n'
                    '```Unknown value for --severity. Valid options are: '
                    'error, warning, info, style```'
                ),
                'issue_opened': True,
                'rich_text': True,
            },
        ])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                '--color=never',
                '--format=json1',
                '--severity=xxx',
                os.path.join(tmpdirs[-1], 'test.sh'),
            ],
            ignore_errors=True)

    @integration_test()
    @simulation_test(output_payload='Invalid number: ABC')
    def test_execute_with_bad_severity_setting(self):
        """Testing ShellCheckTool.execute with bad severity setting"""
        review, review_file = self.run_tool_execute(
            filename='test.sh',
            file_contents=self.SAMPLE_BASH_CODE,
            tool_settings={
                'severity': 'style',
                'exclude': 'ABC',
            })

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 1,
                'num_lines': 1,
                'text': (
                    'The shellcheck returned an unexpected result. Check '
                    'to make sure that your configured settings in Review '
                    'Bot are correct.\n'
                    '\n'
                    'Error message:\n'
                    '```Invalid number: ABC```'
                ),
                'issue_opened': True,
                'rich_text': True,
            },
        ])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                '--color=never',
                '--format=json1',
                '--severity=style',
                '--exclude=ABC',
                os.path.join(tmpdirs[-1], 'test.sh'),
            ],
            ignore_errors=True)

    @integration_test()
    @simulation_test(output_payload={
        'comments': [],
    })
    def test_execute_with_success(self):
        """Testing ShellCheckTool.execute with successful result"""
        review, review_file = self.run_tool_execute(
            filename='test.sh',
            file_contents=(
                b'#!/bin/bash\n'
                b'\n'
                b'echo hi\n'
            ),
            tool_settings={
                'severity': 'style',
            })

        self.assertEqual(review.comments, [])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                '--color=never',
                '--format=json1',
                '--severity=style',
                os.path.join(tmpdirs[-1], 'test.sh'),
            ],
            ignore_errors=True)

    def setup_simulation_test(self, output_payload):
        """Set up the simulation test for shellcheck.

        This will spy on :py:func:`~reviewbot.utils.process.execute`, making
        it return a JSON-serialized string of the provided payload (or the
        payload directly, if it's a string).

        Args:
            output_payload (dict or unicode):
                The payload to output.
        """
        if isinstance(output_payload, dict):
            output_payload = json.dumps(output_payload)

        self.spy_on(execute, op=kgb.SpyOpReturn(output_payload))
