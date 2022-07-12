"""Unit tests for reviewbot.tools.flake8."""

from __future__ import unicode_literals

import json

import kgb
import six

from reviewbot.tools.flake8 import Flake8Tool
from reviewbot.tools.testing import (BaseToolTestCase,
                                     ToolTestCaseMetaclass,
                                     integration_test,
                                     simulation_test)
from reviewbot.utils.process import execute


@six.add_metaclass(ToolTestCaseMetaclass)
class Flake8ToolTests(BaseToolTestCase):
    """Unit tests for reviewbot.tools.flake8.Flake8Tool."""

    tool_class = Flake8Tool
    tool_exe_config_key = 'flake8'
    tool_exe_path = '/path/to/flake8'

    @integration_test()
    @simulation_test(payload={
        './test.py': [
            {
                'categories': ['Style'],
                'check_name': 'F401',
                'description': "'foo' imported but unused",
                'fingerprint': 'c569f8e9d7e983f85811af27d808bbad',
                'location': {
                    'path': './test.py',
                    'positions': {
                        'begin': {
                            'column': 1,
                            'line': 1,
                        },
                        'end': {
                            'column': 1,
                            'line': 1,
                        },
                    },
                },
                'type': 'issue',
            },
            {
                'categories': ['Style'],
                'check_name': 'F821',
                'description': "undefined name 'func'",
                'fingerprint': '68891e77ca330f306ab1feb5c53cc659',
                'location': {
                    'path': './test.py',
                    'positions': {
                        'begin': {
                            'column': 5,
                            'line': 4,
                        },
                        'end': {
                            'column': 5,
                            'line': 4,
                        },
                    },
                },
                'type': 'issue',
            },
            {
                'categories': ['Style'],
                'check_name': 'F841',
                'description': ("local variable 'e' is assigned to but "
                                "never used"),
                'fingerprint': '361546b5a28ad2a813dd439a2cdcac44',
                'location': {
                    'path': './test.py',
                    'positions': {
                        'begin': {
                            'column': 1,
                            'line': 5,
                        },
                        'end': {
                            'column': 1,
                            'line': 5,
                        },
                    },
                },
                'type': 'issue',
            },
        ],
    })
    def test_execute(self):
        """Testing Flake8Tool.execute"""
        review, review_file = self.run_tool_execute(
            filename='test.py',
            file_contents=(
                b'import foo\n'
                b'\n'
                b'try:\n'
                b'    func()\n'
                b'except Exception as e:\n'
                b'    pass\n'
            ),
            tool_settings={
                'max_line_length': 79,
            })

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 1,
                'num_lines': 1,
                'text': (
                    "'foo' imported but unused\n"
                    "\n"
                    "Column: 1\n"
                    "Error code: F401"
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
                    "Column: 5\n"
                    "Error code: F821"
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
                    "Column: 1\n"
                    "Error code: F841"
                ),
                'issue_opened': True,
                'rich_text': False,
            },
        ])

    @integration_test()
    @simulation_test(payload={
        './test.py': [
            {
                'categories': ['Style'],
                'check_name': 'F821',
                'description': "undefined name 'func'",
                'fingerprint': '68891e77ca330f306ab1feb5c53cc659',
                'location': {
                    'path': './test.py',
                    'positions': {
                        'begin': {
                            'column': 5,
                            'line': 4,
                        },
                        'end': {
                            'column': 5,
                            'line': 4,
                        },
                    },
                },
                'type': 'issue',
            },
        ],
    })
    def test_execute_with_ignore(self):
        """Testing Flake8Tool.execute with ignore setting"""
        review, review_file = self.run_tool_execute(
            filename='test.py',
            file_contents=(
                b'import foo\n'
                b'\n'
                b'try:\n'
                b'    func()\n'
                b'except Exception as e:\n'
                b'    pass\n'
            ),
            tool_settings={
                'max_line_length': 79,
                'ignore': 'F841, F401'
            })

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 4,
                'num_lines': 1,
                'text': (
                    "undefined name 'func'\n"
                    "\n"
                    "Column: 5\n"
                    "Error code: F821"
                ),
                'issue_opened': True,
                'rich_text': False,
            },
        ])

    @integration_test()
    @simulation_test(payload={
        './test.py': [
            {
                'categories': ['Style'],
                'check_name': 'E999',
                'description': 'SyntaxError: invalid syntax',
                'fingerprint': 'aba25bd3d9aa80e17f5d6c924cf051bb',
                'location': {
                    'path': './test.py',
                    'positions': {
                        'begin': {
                            'column': 9,
                            'line': 1,
                        },
                        'end': {
                            'column': 9,
                            'line': 1,
                        },
                    },
                },
                'type': 'issue',
            },
        ],
    })
    def test_execute_with_syntax_errors(self):
        """Testing Flake8Tool.execute with syntax errors"""
        review, review_file = self.run_tool_execute(
            filename='test.py',
            file_contents=(
                b'def test:\n'
            ),
            tool_settings={
                'max_line_length': 79,
            })

        self.assertEqual(len(review.comments), 1)
        comment = review.comments[0]

        # Depending on the version of flake8, column indexes may be offset.
        # For wide version compatibility (given current support for Python 2
        # and compatible versions of flake8), this test needs to check both.
        self.assertRegex(
            comment.pop('text'),
            'SyntaxError: invalid syntax\n'
            '\n'
            'Column: (9|10)\n'
            'Error code: E999')

        self.assertEqual(comment, {
            'filediff_id': review_file.id,
            'first_line': 1,
            'num_lines': 1,
            'issue_opened': True,
            'rich_text': False,
        })

    @integration_test()
    @simulation_test(payload={
        './test.py': []
    })
    def test_execute_with_success(self):
        """Testing Flake8Tool.execute with success"""
        review, review_file = self.run_tool_execute(
            filename='test.py',
            file_contents=(
                b'print("Hello, world!")\n'
            ),
            tool_settings={
                'max_line_length': 79,
            })

        self.assertEqual(review.comments, [])

    def setup_simulation_test(self, payload):
        """Set up the simulation test for flake8.

        This will spy on :py:func:`~reviewbot.utils.process.execute`, making
        it return the provided CodeClimate-formatted payload.

        Args:
            payload (dict):
                The CodeClimate-formatted payload to serialize to JSON.
        """
        self.spy_on(execute, op=kgb.SpyOpReturn(json.dumps(payload)))
