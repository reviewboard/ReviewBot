"""Unit tests for reviewbot.tools.pycodestyle."""

from __future__ import annotations

import os

import kgb

from reviewbot.tools.pycodestyle import PycodestyleTool
from reviewbot.tools.testing import (BaseToolTestCase,
                                     ToolTestCaseMetaclass,
                                     integration_test,
                                     simulation_test)
from reviewbot.utils.filesystem import tmpdirs
from reviewbot.utils.process import execute


class BasePycodestyleToolTests(BaseToolTestCase,
                               metaclass=ToolTestCaseMetaclass):
    """Unit tests for reviewbot.tools.pycodestyle.PycodestyleTool."""

    tool_class = PycodestyleTool
    tool_exe_config_key = 'pycodestyle'
    tool_exe_path = '/path/to/pycodestyle'

    @integration_test()
    @simulation_test(output_payload=[
        "E401:1:10:multiple imports on one line",
        "E722:5:1:do not use bare 'except'",
    ])
    def test_execute(self):
        """Testing PycodestyleTool.execute"""
        review, review_file = self.run_tool_execute(
            filename='test.py',
            file_contents=(
                b'import os, sys\n'
                b'\n'
                b'try:\n'
                b'    func()\n'
                b'except:\n'
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
                    'multiple imports on one line\n'
                    '\n'
                    'Column: 10\n'
                    'Error code: E401'
                ),
                'issue_opened': True,
                'rich_text': False,
            },
            {
                'filediff_id': review_file.id,
                'first_line': 5,
                'num_lines': 1,
                'text': (
                    "do not use bare 'except'\n"
                    "\n"
                    "Column: 1\n"
                    "Error code: E722"
                ),
                'issue_opened': True,
                'rich_text': False,
            },
        ])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                '--max-line-length=79',
                '--format=%(code)s:%(row)d:%(col)d:%(text)s',
                os.path.join(tmpdirs[-1], 'test.py'),
            ],
            ignore_errors=True)

    @integration_test()
    @simulation_test(output_payload=[
        "E401:1:10:multiple imports on one line",
    ])
    def test_execute_with_ignore(self):
        """Testing PycodestyleTool.execute with ignore"""
        review, review_file = self.run_tool_execute(
            filename='test.py',
            file_contents=(
                b'import os, sys\n'
                b'\n'
                b'try:\n'
                b'    func()\n'
                b'except:\n'
                b'    pass\n'
            ),
            tool_settings={
                'max_line_length': 79,
                'ignore': 'W123,E722',
            })

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 1,
                'num_lines': 1,
                'text': (
                    'multiple imports on one line\n'
                    '\n'
                    'Column: 10\n'
                    'Error code: E401'
                ),
                'issue_opened': True,
                'rich_text': False,
            },
        ])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                '--max-line-length=79',
                '--format=%(code)s:%(row)d:%(col)d:%(text)s',
                '--ignore=W123,E722',
                os.path.join(tmpdirs[-1], 'test.py'),
            ],
            ignore_errors=True)

    def setup_simulation_test(self, output_payload):
        """Set up the simulation test for pycodestyle.

        This will spy on :py:func:`~reviewbot.utils.process.execute`, making
        it return the provided payload.

        Args:
            output_payload (dict):
                The outputted payload.
        """
        self.spy_on(execute, op=kgb.SpyOpReturn(output_payload))
