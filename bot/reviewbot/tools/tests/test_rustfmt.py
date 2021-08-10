"""Unit tests for reviewbot.tools.rustfmt."""

from __future__ import unicode_literals

import os

import kgb
import six

from reviewbot.tools.rustfmt import RustfmtTool
from reviewbot.tools.testing import (BaseToolTestCase,
                                     ToolTestCaseMetaclass,
                                     integration_test,
                                     simulation_test)
from reviewbot.utils.filesystem import tmpdirs
from reviewbot.utils.process import execute


@six.add_metaclass(ToolTestCaseMetaclass)
class RustfmtToolTests(BaseToolTestCase):
    """Unit tests for reviewbot.tools.rustfmt.RustfmtTool."""

    tool_class = RustfmtTool
    tool_exe_config_key = 'rustfmt'
    tool_exe_path = '/path/to/rustfmt'

    @integration_test()
    @simulation_test(stdout=(
        'Diff in /test.rs at line 1:\n'
        ' fn main() {\n'
        '-println!("Hi")\n'
        '+    println!("Hi")\n'
        '}\n'
    ))
    def test_execute(self):
        """Testing RustfmtTool.execute"""
        review, review_file = self.run_tool_execute(
            filename='test.rs',
            file_contents=(
                b'fn main() {\n'
                b'println!("Hi")\n'
                b'}\n'
            ))

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 1,
                'num_lines': 1,
                'text': (
                    'This file contains formatting errors and should be run '
                    'through `rustfmt`.'
                ),
                'issue_opened': True,
                'rich_text': True,
            },
        ])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                '-q',
                '--check',
                '--color=never',
                os.path.join(tmpdirs[-1], 'test.rs'),
            ],
            ignore_errors=True,
            return_errors=True)

    @integration_test()
    @simulation_test(stderr=(
        'error: this file contains an unclosed delimiter\n'
        ' --> /test.rs:2:27\n'
        '  |\n'
        '1 | afn main() {\n'
        '               - unclosed delimiter\n'
        '2 | println!("Hello world!");\n'
        '  |                           ^\n'
        '\n'
        'error: expected one of `!` or `::`, found `main`\n'
        ' --> /test.rs:1:6\n'
        '  |\n'
        '1 | afn main() {\n'
        '  |     ^^^^ expected one of `!` or `::`\n'
    ))
    def test_execute_with_syntax_error(self):
        """Testing RustfmtTool.execute with syntax error"""
        review, review_file = self.run_tool_execute(
            filename='test.rs',
            file_contents=(
                b'func main() {}\n'
            ))

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 1,
                'num_lines': 1,
                'text': (
                    'expected one of `!` or `::`, found `main`\n'
                    '\n'
                    'Column: 6'
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
                '--check',
                '--color=never',
                os.path.join(tmpdirs[-1], 'test.rs'),
            ],
            ignore_errors=True,
            return_errors=True)

    @integration_test()
    @simulation_test()
    def test_execute_with_success(self):
        """Testing RustfmtTool.execute with no errors"""
        review, review_file = self.run_tool_execute(
            filename='test.rs',
            file_contents=(
                b'fn main() {\n'
                b'    println!("Hello world!");\n'
                b'}\n'
            ))

        self.assertEqual(review.comments, [])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                '-q',
                '--check',
                '--color=never',
                os.path.join(tmpdirs[-1], 'test.rs'),
            ],
            ignore_errors=True,
            return_errors=True)

    def setup_simulation_test(self, stdout='', stderr=''):
        """Set up the simulation test for rustfmt.

        This will spy on :py:func:`~reviewbot.utils.process.execute`, making
        it return the provided stdout and stderr results.

        Args:
            stdout (unicode, optional):
                The outputted stdout.

            stderr (unicode, optional):
                The outputted stderr.
        """
        self.spy_on(execute, op=kgb.SpyOpReturn((stdout, stderr)))
