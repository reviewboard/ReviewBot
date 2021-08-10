"""Unit tests for reviewbot.tools.pydocstyle."""

from __future__ import unicode_literals

import os

import kgb
import six

from reviewbot.tools.pydocstyle import PydocstyleTool
from reviewbot.tools.testing import (BaseToolTestCase,
                                     ToolTestCaseMetaclass,
                                     integration_test,
                                     simulation_test)
from reviewbot.utils.filesystem import tmpdirs
from reviewbot.utils.process import execute


@six.add_metaclass(ToolTestCaseMetaclass)
class PydocstyleToolTests(BaseToolTestCase):
    """Unit tests for reviewbot.tools.pydocstyle.PydocstyleTool."""

    tool_class = PydocstyleTool
    tool_exe_config_key = 'pydocstyle'
    tool_exe_path = '/path/to/pydocstyle'

    @integration_test()
    @simulation_test(output=(
        '/path/to/test.py:1 at module level:\n'
        '        D100: Missing docstring in public module\n'
        '/path/to/test.py:1 in public function `test1`:\n'
        '        D103: Missing docstring in public function\n'
        '/path/to/test.py:5 in public function `test2`:\n'
        '        D300: Use """triple double quotes""" (found \'\'\'-quotes)\n'
        '/path/to/test.py:5 in public function `test2`:\n'
        '        D400: First line should end with a period (not \'s\')\n'
    ))
    def test_execute(self):
        """Testing PydocstyleTool.execute"""
        review, review_file = self.run_tool_execute(
            filename='test.py',
            file_contents=(
                b"def test1():\n"
                b"    pass\n"
                b"\n"
                b"def test2():\n"
                b"    '''Invalid for many reasons'''\n"
            ))

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 1,
                'num_lines': 1,
                'text': (
                    'Missing docstring in public module\n'
                    '\n'
                    'Error code: D100'
                ),
                'issue_opened': True,
                'rich_text': False,
            },
            {
                'filediff_id': review_file.id,
                'first_line': 1,
                'num_lines': 1,
                'text': (
                    'Missing docstring in public function\n'
                    '\n'
                    'Error code: D103'
                ),
                'issue_opened': True,
                'rich_text': False,
            },
            {
                'filediff_id': review_file.id,
                'first_line': 5,
                'num_lines': 1,
                'text': (
                    'Use """triple double quotes""" (found \'\'\'-quotes)\n'
                    '\n'
                    'Error code: D300'
                ),
                'issue_opened': True,
                'rich_text': False,
            },
            {
                'filediff_id': review_file.id,
                'first_line': 5,
                'num_lines': 1,
                'text': (
                    "First line should end with a period (not 's')\n"
                    "\n"
                    "Error code: D400"
                ),
                'issue_opened': True,
                'rich_text': False,
            },
        ])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                os.path.join(tmpdirs[-1], 'test.py'),
            ],
            ignore_errors=True)

    @integration_test()
    @simulation_test(output=(
        '/path/to/test.py:1 in public function `test1`:\n'
        '        D103: Missing docstring in public function\n'
        '/path/to/test.py:5 in public function `test2`:\n'
        '        D300: Use """triple double quotes""" (found \'\'\'-quotes)\n'
        '/path/to/test.py:5 in public function `test2`:\n'
        '        D415: First line should end with a period, question mark, or '
        'exclamation point (not \'s\')\n'
    ))
    def test_execute_with_ignore(self):
        """Testing PydocstyleTool.execute with ignore setting"""
        review, review_file = self.run_tool_execute(
            filename='test.py',
            file_contents=(
                b"def test1():\n"
                b"    pass\n"
                b"\n"
                b"def test2():\n"
                b"    '''Invalid for many reasons'''\n"
            ),
            tool_settings={
                'ignore': 'D100, D400',
            })

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 1,
                'num_lines': 1,
                'text': (
                    'Missing docstring in public function\n'
                    '\n'
                    'Error code: D103'
                ),
                'issue_opened': True,
                'rich_text': False,
            },
            {
                'filediff_id': review_file.id,
                'first_line': 5,
                'num_lines': 1,
                'text': (
                    'Use """triple double quotes""" (found \'\'\'-quotes)\n'
                    '\n'
                    'Error code: D300'
                ),
                'issue_opened': True,
                'rich_text': False,
            },
            {
                'filediff_id': review_file.id,
                'first_line': 5,
                'num_lines': 1,
                'text': (
                    "First line should end with a period, question mark, or "
                    "exclamation point (not 's')\n"
                    "\n"
                    "Error code: D415"
                ),
                'issue_opened': True,
                'rich_text': False,
            },
        ])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                '--ignore=D100, D400',
                os.path.join(tmpdirs[-1], 'test.py'),
            ],
            ignore_errors=True)

    @integration_test()
    @simulation_test(output='')
    def test_execute_with_success(self):
        """Testing PydocstyleTool.execute with no errors"""
        review, review_file = self.run_tool_execute(
            filename='test.py',
            file_contents=(
                b'"""Module docstring."""\n'
                b'\n'
                b'def test():\n'
                b'    """Function docstring."""\n'
            ))

        self.assertEqual(review.comments, [])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                os.path.join(tmpdirs[-1], 'test.py'),
            ],
            ignore_errors=True)

    def setup_simulation_test(self, output=[]):
        """Set up the simulation test for pyflakes.

        This will spy on :py:func:`~reviewbot.utils.process.execute`, making
        it return the provided output.

        Args:
            output (unicode):
                The simulatedo output from the tool.
        """
        self.spy_on(execute, op=kgb.SpyOpReturn(output))
