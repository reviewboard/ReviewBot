"""Unit tests for reviewbot.tools.rubocop."""

from __future__ import unicode_literals

import json
import os
import re

import kgb
import six

from reviewbot.tools.rubocop import RubocopTool
from reviewbot.tools.testing import (BaseToolTestCase,
                                     ToolTestCaseMetaclass,
                                     integration_test,
                                     simulation_test)
from reviewbot.utils.filesystem import tmpdirs
from reviewbot.utils.process import execute


@six.add_metaclass(ToolTestCaseMetaclass)
class RubocopToolTests(BaseToolTestCase):
    """Unit tests for reviewbot.tools.rubocop.RubocopTool."""

    tool_class = RubocopTool
    tool_exe_config_key = 'rubocop'
    tool_exe_path = '/path/to/rubocop'

    SAMPLE_RUBY_CODE = (
        b'# frozen_string_literal: true\n'
        b'\n'
        b'def testFunc\n'
        b'  if foo\n'
        b'    test\n'
        b'    test2\n'
        b'    end\n'
        b'end\n'
    )

    @integration_test()
    @simulation_test(output_payload={
        'files': [
            {
                'offenses': [
                    {
                        'cop_name': 'Naming/MethodName',
                        'correctable': False,
                        'corrected': False,
                        'location': {
                            'column': 5,
                            'last_column': 12,
                            'last_line': 3,
                            'length': 8,
                            'line': 3,
                            'start_column': 5,
                            'start_line': 3,
                        },
                        'message': (
                            'Naming/MethodName: Use snake_case for method '
                            'names. (https://rubystyle.guide'
                            '#snake-case-symbols-methods-vars)'
                        ),
                        'severity': 'convention',
                    },
                    {
                        'cop_name': 'Style/GuardClause',
                        'correctable': False,
                        'corrected': False,
                        'location': {
                            'column': 3,
                            'last_column': 4,
                            'last_line': 4,
                            'length': 2,
                            'line': 4,
                            'start_column': 3,
                            'start_line': 4,
                        },
                        'message': (
                            'Style/GuardClause: Use a guard clause (`return '
                            'unless foo`) instead of wrapping the code '
                            'inside a conditional expression. '
                            '(https://rubystyle.guide#no-nested-conditionals)'
                        ),
                        'severity': 'convention',
                    },
                    {
                        'cop_name': 'Layout/EndAlignment',
                        'correctable': True,
                        'corrected': False,
                        'location': {
                            'column': 5,
                            'last_column': 7,
                            'last_line': 7,
                            'length': 3,
                            'line': 7,
                            'start_column': 5,
                            'start_line': 7,
                        },
                        'message': (
                            'Layout/EndAlignment: `end` at 7, 4 is not '
                            'aligned with `if` at 4, 2.'
                        ),
                        'severity': 'warning',
                    },
                ],
                'path': '/test.rb',
            },
        ],
        'summary': {
            'inspected_file_count': 1,
            'offense_count': 3,
            'target_file_count': 1,
        },
    })
    def test_execute(self):
        """Testing RubocopTool.execute"""
        review, review_file = self.run_tool_execute(
            filename='test.rb',
            file_contents=self.SAMPLE_RUBY_CODE)

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 3,
                'num_lines': 1,
                'text': (
                    'Use snake_case for method names. (https://rubystyle.guide'
                    '#snake-case-symbols-methods-vars)\n'
                    '\n'
                    'Column: 5\n'
                    'Severity: convention\n'
                    'Error code: Naming/MethodName'
                ),
                'issue_opened': True,
                'rich_text': True,
            },
            {
                'filediff_id': review_file.id,
                'first_line': 4,
                'num_lines': 1,
                'text': (
                    'Use a guard clause (`return unless foo`) instead of '
                    'wrapping the code inside a conditional expression. '
                    '(https://rubystyle.guide#no-nested-conditionals)\n'
                    '\n'
                    'Column: 3\n'
                    'Severity: convention\n'
                    'Error code: Style/GuardClause'
                ),
                'issue_opened': True,
                'rich_text': True,
            },
            {
                'filediff_id': review_file.id,
                'first_line': 7,
                'num_lines': 1,
                'text': (
                    '`end` at 7, 4 is not aligned with `if` at 4, 2.\n'
                    '\n'
                    'Column: 5\n'
                    'Severity: warning\n'
                    'Error code: Layout/EndAlignment'
                ),
                'issue_opened': True,
                'rich_text': True,
            },
        ])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                '--format=json',
                '--display-style-guide',
                os.path.join(tmpdirs[-1], 'test.rb'),
            ],
            ignore_errors=True)

    @integration_test()
    @simulation_test(output_payload={
        'files': [
            {
                'offenses': [
                    {
                        'cop_name': 'Naming/MethodName',
                        'corrected': False,
                        'location': {
                            'column': 5,
                            'length': 8,
                            'line': 3,
                        },
                        'message': (
                            'Naming/MethodName: Use snake_case for method '
                            'names. (https://rubystyle.guide'
                            '#snake-case-symbols-methods-vars)'
                        ),
                        'severity': 'convention',
                    },
                    {
                        'cop_name': 'Style/GuardClause',
                        'corrected': False,
                        'location': {
                            'column': 3,
                            'length': 2,
                            'line': 4,
                        },
                        'message': (
                            'Use a guard clause (`return unless foo`) '
                            'instead of wrapping the code inside a '
                            'conditional expression. '
                            '(https://rubystyle.guide#no-nested-conditionals)'
                        ),
                        'severity': 'convention',
                    },
                    {
                        'cop_name': 'Layout/EndAlignment',
                        'corrected': False,
                        'location': {
                            'column': 5,
                            'length': 3,
                            'line': 7,
                        },
                        'message': (
                            '`end` at 7, 4 is not aligned with `if` at 4, 2.'
                        ),
                        'severity': 'warning',
                    },
                ],
                'path': '/test.rb',
            },
        ],
        'summary': {
            'inspected_file_count': 1,
            'offense_count': 3,
            'target_file_count': 1,
        },
    })
    def test_execute_with_legacy_offenses(self):
        """Testing RubocopTool.execute with legacy offense information"""
        review, review_file = self.run_tool_execute(
            filename='test.rb',
            file_contents=self.SAMPLE_RUBY_CODE)

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 3,
                'num_lines': 1,
                'text': (
                    'Use snake_case for method names. (https://rubystyle.guide'
                    '#snake-case-symbols-methods-vars)\n'
                    '\n'
                    'Column: 5\n'
                    'Severity: convention\n'
                    'Error code: Naming/MethodName'
                ),
                'issue_opened': True,
                'rich_text': True,
            },
            {
                'filediff_id': review_file.id,
                'first_line': 4,
                'num_lines': 1,
                'text': (
                    'Use a guard clause (`return unless foo`) instead of '
                    'wrapping the code inside a conditional expression. '
                    '(https://rubystyle.guide#no-nested-conditionals)\n'
                    '\n'
                    'Column: 3\n'
                    'Severity: convention\n'
                    'Error code: Style/GuardClause'
                ),
                'issue_opened': True,
                'rich_text': True,
            },
            {
                'filediff_id': review_file.id,
                'first_line': 7,
                'num_lines': 1,
                'text': (
                    '`end` at 7, 4 is not aligned with `if` at 4, 2.\n'
                    '\n'
                    'Column: 5\n'
                    'Severity: warning\n'
                    'Error code: Layout/EndAlignment'
                ),
                'issue_opened': True,
                'rich_text': True,
            },
        ])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                '--format=json',
                '--display-style-guide',
                os.path.join(tmpdirs[-1], 'test.rb'),
            ],
            ignore_errors=True)

    @integration_test()
    @simulation_test(output_payload={
        'files': [
            {
                'offenses': [
                    {
                        'cop_name': 'Naming/MethodName',
                        'correctable': False,
                        'corrected': False,
                        'location': {
                            'column': 5,
                            'last_column': 12,
                            'last_line': 3,
                            'length': 8,
                            'line': 3,
                            'start_column': 5,
                            'start_line': 3,
                        },
                        'message': (
                            'Naming/MethodName: Use snake_case for method '
                            'names. (https://rubystyle.guide'
                            '#snake-case-symbols-methods-vars)'
                        ),
                        'severity': 'convention',
                    },
                ],
                'path': '/test.rb',
            },
        ],
        'summary': {
            'inspected_file_count': 1,
            'offense_count': 1,
            'target_file_count': 1,
        },
    })
    def test_execute_with_except(self):
        """Testing RubocopTool.execute with except setting"""
        review, review_file = self.run_tool_execute(
            filename='test.rb',
            file_contents=self.SAMPLE_RUBY_CODE,
            tool_settings={
                'except': 'Layout/EndAlignment, Style/GuardClause',
            })

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 3,
                'num_lines': 1,
                'text': (
                    'Use snake_case for method names. (https://rubystyle.guide'
                    '#snake-case-symbols-methods-vars)\n'
                    '\n'
                    'Column: 5\n'
                    'Severity: convention\n'
                    'Error code: Naming/MethodName'
                ),
                'issue_opened': True,
                'rich_text': True,
            },
        ])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                '--format=json',
                '--display-style-guide',
                '--except=Layout/EndAlignment,Style/GuardClause',
                os.path.join(tmpdirs[-1], 'test.rb'),
            ],
            ignore_errors=True)

    @integration_test()
    @simulation_test(output_payload=(
        'Unrecognized cop or department: XXXBAD.\n'
        '{}'
    ))
    def test_execute_with_bad_except(self):
        """Testing RubocopTool.execute with bad except setting"""
        review, review_file = self.run_tool_execute(
            filename='test.rb',
            file_contents=self.SAMPLE_RUBY_CODE,
            tool_settings={
                'except': 'XXXBAD',
            })

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 1,
                'num_lines': 1,
                'text': (
                    'RuboCop could not analyze this file, due to the '
                    'following errors:\n'
                    '\n'
                    '```Unrecognized cop or department: XXXBAD.```'
                ),
                'issue_opened': True,
                'rich_text': True,
            },
        ])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                '--format=json',
                '--display-style-guide',
                '--except=XXXBAD',
                os.path.join(tmpdirs[-1], 'test.rb'),
            ],
            ignore_errors=True)

    @integration_test()
    @simulation_test(output_payload={
        'files': [
            {
                'offenses': [
                    {
                        'cop_name': 'Lint/Syntax',
                        'correctable': False,
                        'corrected': False,
                        'location': {
                            'column': 3,
                            'last_column': 3,
                            'last_line': 1,
                            'length': 1,
                            'line': 1,
                            'start_column': 3,
                            'start_line': 1,
                        },
                        'message': (
                            'unexpected token tRBRACK\n'
                            '(Using Ruby 2.4 parser; configure using '
                            '`TargetRubyVersion` parameter, under `AllCops`)'
                        ),
                        'severity': 'error',
                    },
                ],
                'path': '/test.rb',
            },
        ],
        'summary': {
            'inspected_file_count': 1,
            'offense_count': 1,
            'target_file_count': 1,
        },
    })
    def test_execute_with_syntax_error(self):
        """Testing RubocopTool.execute with syntax error"""
        review, review_file = self.run_tool_execute(
            filename='test.rb',
            file_contents=b'{{]]')

        self.assertNotEqual(review.comments, [])

        # Normalize the Ruby version number in the result, for comparison.
        review.comments[0]['text'] = re.sub(r'Ruby \d+.\d+',
                                            'Ruby X.Y',
                                            review.comments[0]['text'])

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 1,
                'num_lines': 1,
                'text': (
                    'unexpected token tRBRACK\n'
                    '(Using Ruby X.Y parser; configure using '
                    '`TargetRubyVersion` parameter, under `AllCops`)\n'
                    '\n'
                    'Column: 3\n'
                    'Severity: error\n'
                    'Error code: Lint/Syntax'
                ),
                'issue_opened': True,
                'rich_text': True,
            },
        ])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                '--format=json',
                '--display-style-guide',
                os.path.join(tmpdirs[-1], 'test.rb'),
            ],
            ignore_errors=True)

    @integration_test()
    @simulation_test(output_payload={
        'files': [
            {
                'offenses': [],
                'path': '/test.rb',
            },
        ],
        'summary': {
            'inspected_file_count': 1,
            'offense_count': 0,
            'target_file_count': 1,
        },
    })
    def test_execute_with_success(self):
        """Testing RubocopTool.execute with successful result"""
        review, review_file = self.run_tool_execute(
            filename='test.rb',
            file_contents=(
                b'# frozen_string_literal: true\n'
                b'\n'
                b'def test1\n'
                b'  test2\n'
                b'  test3\n'
                b'end\n'
            ))

        self.assertEqual(review.comments, [])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                '--format=json',
                '--display-style-guide',
                os.path.join(tmpdirs[-1], 'test.rb'),
            ],
            ignore_errors=True)

    def setup_simulation_test(self, output_payload):
        """Set up the simulation test for rubocop.

        This will spy on :py:func:`~reviewbot.utils.process.execute`, making
        it return the provided payload (serializing to JSON if a dictionary).

        Args:
            output_payload (dict or unicode):
                The payload to return.
        """
        if isinstance(output_payload, dict):
            output_payload = json.dumps(output_payload)

        self.spy_on(execute, op=kgb.SpyOpReturn(output_payload))
