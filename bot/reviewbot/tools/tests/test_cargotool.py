"""Unit tests for reviewbot.tools.cargotool."""

from __future__ import unicode_literals

import json
import os
import tempfile

import kgb
import six

from reviewbot.tools.cargotool import CargoTool
from reviewbot.tools.testing import (BaseToolTestCase,
                                     ToolTestCaseMetaclass,
                                     integration_test,
                                     simulation_test)
from reviewbot.utils.process import execute


@six.add_metaclass(ToolTestCaseMetaclass)
class CargoToolTests(BaseToolTestCase):
    """Unit tests for reviewbot.tools.cargotool.CargoTool."""

    tool_class = CargoTool
    tool_exe_config_key = 'cargo'
    tool_exe_path = '/path/to/cargo'

    BAD_RS_CODE1 = (
        b'fn main() {\n'
        b'    println("Hi")\n'
        b'}\n'
    )

    BAD_RS_CODE2 = (
        b'fn main() {\n'
        b'    foo()\n'
        b'}\n'
    )

    GOOD_RS_CODE1 = (
        b'fn main() {\n'
        b'    println!("Hi")\n'
        b'}\n'
    )

    GOOD_RS_CODE2 = (
        b'fn main() {\n'
        b'    println!("Bye!")\n'
        b'}\n'
    )

    BAD_RS_1_TEST = (
        b'mod tests {\n'
        b'    #[test]\n'
        b'    fn test1() {\n'
        b'        assert_eq!(1, 2)\n'
        b'    }\n'
        b'}\n'
    )

    BAD_RS_N_TESTS = (
        b'mod tests {\n'
        b'    #[test]\n'
        b'    fn test1() {\n'
        b'        assert_eq!(1, 2)\n'
        b'    }\n'
        b'\n'
        b'    #[test]\n'
        b'    fn test2() {\n'
        b'        assert_eq!(3, 4)\n'
        b'    }\n'
        b'}\n'
    )

    BAD_RS_TESTS_SYNTAX_ERROR = (
        b'mod tests {\n'
        b'    #[test]\n'
        b'    fn test1() {\n'
        b'        assert_eq!(1, 2)\n'
        b'\n'
        b'    #[test]\n'
        b'    fn test2() {\n'
        b'        assert_eq!(3, 4)\n'
        b'    }\n'
    )

    GOOD_RS_TESTS = (
        b'mod tests {\n'
        b'    #[test]\n'
        b'    fn test1() {\n'
        b'        assert_eq!(1, 1)\n'
        b'    }\n'
        b'\n'
        b'    #[test]\n'
        b'    fn test2() {\n'
        b'        assert_eq!(2, 2)\n'
        b'    }\n'
        b'}\n'
    )

    def setUp(self):
        super(CargoToolTests, self).setUp()

        self.checkout_dir = tempfile.mkdtemp()

        with open(os.path.join(self.checkout_dir, 'Cargo.toml'), 'w') as fp:
            fp.write('[package]\n'
                     'name = "test"\n'
                     'version = "1.0.0"\n'
                     '\n'
                     '[[bin]]\n'
                     'name = "main"\n'
                     'path = "main.rs"\n'
                     '\n'
                     '[[bin]]\n'
                     'name = "main2"\n'
                     'path = "main2.rs"\n')

    # NOTE: Payloads here only contain the data we need for our tests.
    @integration_test()
    @simulation_test(output=[
        json.dumps({
           'message': {
              'code': {
                 'code': 'E0423',
              },
              'level': 'error',
              'message': 'expected function, found macro `println`',
              'spans': [
                 {
                    'column_end': 12,
                    'column_start': 5,
                    'line_end': 2,
                    'line_start': 2,
                 },
              ],
           },
           'reason': 'compiler-message',
           'target': {
              'name': 'main',
              'src_path': '%(checkout_dir)s/main.rs',
           },
        }),
        '\n',
        json.dumps({
           'message': {
              'code': {
                 'code': 'E0425',
              },
              'level': 'error',
              'message': 'cannot find function `foo` in this scope',
              'spans': [
                 {
                    'column_end': 8,
                    'column_start': 5,
                    'line_end': 2,
                    'line_start': 2,
                 },
              ],
           },
           'reason': 'compiler-message',
           'target': {
              'name': 'main2',
              'src_path': '%(checkout_dir)s/main2.rs',
           },
        }),
        '\n',
        json.dumps({
           'message': {
              'code': None,
              'level': 'error',
              'message': 'aborting due to previous error',
              'spans': [],
           },
           'reason': 'compiler-message',
           'target': {
              'name': 'main2',
              'src_path': '%(checkout_dir)s/main2.rs',
           },
        }),
        '\n',
        json.dumps({
           'message': {
              'code': None,
              'level': 'error',
              'message': 'aborting due to previous error',
              'spans': [],
           },
           'reason': 'compiler-message',
           'target': {
              'name': 'main',
              'src_path': '%(checkout_dir)s/main.rs',
           },
        }),
        '\n',
        json.dumps({
           'message': {
              'code': None,
              'level': 'failure-note',
              'message': ('For more information about this error, try '
                          '`rustc --explain E0425`.'),
              'spans': [],
           },
           'reason': 'compiler-message',
           'target': {
              'name': 'main2',
              'src_path': '%(checkout_dir)s/main2.rs',
           },
        }),
        '\n',
        json.dumps({
           'message': {
              'code': None,
              'level': 'failure-note',
              'message': ('For more information about this error, try '
                          '`rustc --explain E0423`.'),
              'spans': []
           },
           'reason': 'compiler-message',
           'target': {
              'name': 'main',
              'src_path': '%(checkout_dir)s/main.rs',
           },
        }),
        '\n',
        json.dumps({
            'reason': 'build-finished',
            'success': False,
        }),
    ])
    def test_execute_with_clippy_true(self):
        """Testing CargoTool.execute with clippy=True and > 0 issues"""
        review, review_files = self.run_tool_execute(
            checkout_dir=self.checkout_dir,
            filename='main.rs',
            file_contents=self.BAD_RS_CODE1,
            other_files={
                'main2.rs': self.BAD_RS_CODE2,
            },
            tool_settings={
                'clippy': True,
            })

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_files['main.rs'].id,
                'first_line': 2,
                'num_lines': 1,
                'text': (
                    'expected function, found macro `println`\n'
                    '\n'
                    'Column: 5\n'
                    'Severity: error\n'
                    'Error code: E0423'
                ),
                'issue_opened': True,
                'rich_text': True,
            },
            {
                'filediff_id': review_files['main2.rs'].id,
                'first_line': 2,
                'num_lines': 1,
                'text': (
                    'cannot find function `foo` in this scope\n'
                    '\n'
                    'Column: 5\n'
                    'Severity: error\n'
                    'Error code: E0425'
                ),
                'issue_opened': True,
                'rich_text': True,
            },
        ])
        self.assertEqual(review.general_comments, [])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                'clippy',
                '-q',
                '--message-format=json',
                '--tests',
            ],
            split_lines=True,
            with_errors=False,
            ignore_errors=True)

    @integration_test()
    @simulation_test(output=[
        json.dumps({
            'reason': 'build-finished',
            'success': True,
        }),
    ])
    def test_execute_with_clippy_true_and_0_issues(self):
        """Testing CargoTool.execute with clippy=True and 0 issues"""
        review, review_files = self.run_tool_execute(
            checkout_dir=self.checkout_dir,
            filename='main.rs',
            file_contents=self.GOOD_RS_CODE1,
            other_files={
                'main2.rs': self.GOOD_RS_CODE2,
            },
            tool_settings={
                'clippy': True,
            })

        self.assertEqual(review.comments, [])
        self.assertEqual(review.general_comments, [])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                'clippy',
                '-q',
                '--message-format=json',
                '--tests',
            ],
            split_lines=True,
            with_errors=False,
            ignore_errors=True)

    @integration_test()
    @simulation_test(output=[
        "running 0 tests\n",
        "\n",
        "test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured;"
        " 0 filtered out; finished in 0.00s\n",
        "\n",
        "running 0 tests\n",
        "\n",
        "test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured;"
        " 0 filtered out; finished in 0.00s\n",
        "\n",
        "running 1 tests\n",
        "FF\n",
        "failures:\n",
        "\n",
        "---- tests::test1 stdout ----\n",
        "thread 'main' panicked at 'assertion failed: `(left == right)`\n",
        "  left: `1`,\n",
        " right: `2`', tests/test.rs:4:9\n",
        "note: run with `RUST_BACKTRACE=1` environment variable to display"
        " a backtrace\n",
        "\n",
        "\n",
        "failures:\n",
        "    tests::test1\n",
        "\n",
        "test result: FAILED. 0 passed; 1 failed; 0 ignored; 0 measured;"
        " 0 filtered out; finished in 0.00s\n",
        "\n",
        "error: test failed, to rerun pass '--test test'\n",
    ])
    def test_execute_with_test_true_1_failed(self):
        """Testing CargoTool.execute with test=True and 1 failure"""
        review, review_files = self.run_tool_execute(
            checkout_dir=self.checkout_dir,
            filename='main.rs',
            file_contents=self.GOOD_RS_CODE1,
            other_files={
                'main2.rs': self.GOOD_RS_CODE2,
                'tests/test.rs': self.BAD_RS_1_TEST,
            },
            tool_settings={
                'test': True,
            })

        self.assertEqual(review.comments, [])
        self.assertEqual(review.general_comments, [
            {
                'issue_opened': True,
                'rich_text': True,
                'text': (
                    "1 test failed:\n"
                    "\n"
                    "```"
                    "---- tests::test1 stdout ----\n"
                    "thread 'main' panicked at 'assertion failed: "
                    "`(left == right)`\n"
                    "  left: `1`,\n"
                    " right: `2`', tests/test.rs:4:9\n"
                    "\n"
                    "\n"
                    "failures:\n"
                    "    tests::test1"
                    "```"
                )
            },
        ])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                '-q',
                'test',
                '--',
                '--test-threads=1',
            ],
            with_errors=True,
            ignore_errors=True)

    @integration_test()
    @simulation_test(output=[
        "running 0 tests\n",
        "\n",
        "test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured;"
        " 0 filtered out; finished in 0.00s\n",
        "\n",
        "running 0 tests\n",
        "\n",
        "test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured;"
        " 0 filtered out; finished in 0.00s\n",
        "\n",
        "running 2 tests\n",
        "FF\n",
        "failures:\n",
        "\n",
        "---- tests::test1 stdout ----\n",
        "thread 'main' panicked at 'assertion failed: `(left == right)`\n",
        "  left: `1`,\n",
        " right: `2`', tests/test.rs:4:9\n",
        "note: run with `RUST_BACKTRACE=1` environment variable to display"
        " a backtrace\n",
        "\n",
        "---- tests::test2 stdout ----\n",
        "thread 'main' panicked at 'assertion failed: `(left == right)`\n",
        "  left: `3`,\n",
        " right: `4`', tests/test.rs:9:9\n",
        "note: run with `RUST_BACKTRACE=1` environment variable to display"
        " a backtrace\n",
        "\n",
        "\n",
        "failures:\n",
        "    tests::test1\n",
        "    tests::test2\n",
        "\n",
        "test result: FAILED. 0 passed; 2 failed; 0 ignored; 0 measured;"
        " 0 filtered out; finished in 0.00s\n",
        "\n",
        "error: test failed, to rerun pass '--test test'\n",
    ])
    def test_execute_with_test_true_gt_1_failures(self):
        """Testing CargoTool.execute with test=True and > 1 failures"""
        review, review_files = self.run_tool_execute(
            checkout_dir=self.checkout_dir,
            filename='main.rs',
            file_contents=self.GOOD_RS_CODE1,
            other_files={
                'main2.rs': self.GOOD_RS_CODE2,
                'tests/test.rs': self.BAD_RS_N_TESTS,
            },
            tool_settings={
                'test': True,
            })

        self.assertEqual(review.comments, [])
        self.assertEqual(review.general_comments, [
            {
                'issue_opened': True,
                'rich_text': True,
                'text': (
                    "2 tests failed:\n"
                    "\n"
                    "```"
                    "---- tests::test1 stdout ----\n"
                    "thread 'main' panicked at 'assertion failed: "
                    "`(left == right)`\n"
                    "  left: `1`,\n"
                    " right: `2`', tests/test.rs:4:9\n"
                    "\n"
                    "---- tests::test2 stdout ----\n"
                    "thread 'main' panicked at 'assertion failed: "
                    "`(left == right)`\n"
                    "  left: `3`,\n"
                    " right: `4`', tests/test.rs:9:9\n"
                    "\n"
                    "\n"
                    "failures:\n"
                    "    tests::test1\n"
                    "    tests::test2"
                    "```"
                )
            },
        ])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                '-q',
                'test',
                '--',
                '--test-threads=1',
            ],
            with_errors=True,
            ignore_errors=True)

    @integration_test()
    @simulation_test(output=[
        "running 0 tests\n",
        "\n",
        "test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured;"
        " 0 filtered out; finished in 0.00s\n",
        "\n",
        "running 0 tests\n",
        "\n",
        "test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured;"
        " 0 filtered out; finished in 0.00s\n",
        "\n",
        "running 0 tests\n",
        "\n",
        "test result: ok. 2 passed; 0 failed; 0 ignored; 0 measured;"
        " 0 filtered out; finished in 0.00s\n",
    ])
    def test_execute_with_test_true_0_failures(self):
        """Testing CargoTool.execute with test=True and 0 failures"""
        review, review_files = self.run_tool_execute(
            checkout_dir=self.checkout_dir,
            filename='main.rs',
            file_contents=self.GOOD_RS_CODE1,
            other_files={
                'main2.rs': self.GOOD_RS_CODE2,
                'tests/test.rs': self.GOOD_RS_TESTS,
            },
            tool_settings={
                'test': True,
            })

        self.assertEqual(review.comments, [])
        self.assertEqual(review.general_comments, [])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                '-q',
                'test',
                '--',
                '--test-threads=1',
            ],
            with_errors=True,
            ignore_errors=True)

    @simulation_test(output=[
        "running 0 tests\n",
        "\n",
        "test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured;"
        " 0 filtered out; finished in 0.00s\n",
        "\n",
        "running 0 tests\n",
        "\n",
        "test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured;"
        " 0 filtered out; finished in 0.00s\n",
        "\n",
        "running 2 tests\n",
        "FF\n",
        "failures:\n",
        "\n",
        "---- tests::test1 stdout ----\n",
        "thread 'main' panicked at 'assertion failed: `(left == right)`\n",
        "  left: `1`,\n",
        " right: `2`', tests/test.rs:4:9\n",
    ] + [
        'line %s\n' % _i
        for _i in range(1, 200)
    ] + [
        "\n",
        "\n",
        "\n",
        "failures:\n",
        "    tests::test1\n",
        "\n",
        "test result: FAILED. 0 passed; 1 failed; 0 ignored; 0 measured;"
        " 0 filtered out; finished in 0.00s\n",
        "\n",
        "error: test failed, to rerun pass '--test test'\n",
    ])
    def test_execute_with_test_true_and_line_cap(self):
        """Testing CargoTool.execute with test=True and line cap hit"""
        review, review_files = self.run_tool_execute(
            checkout_dir=self.checkout_dir,
            filename='main.rs',
            file_contents=self.GOOD_RS_CODE1,
            other_files={
                'main2.rs': self.GOOD_RS_CODE2,
                'tests/test.rs': self.BAD_RS_1_TEST,
            },
            tool_settings={
                'test': True,
            })

        self.assertEqual(review.comments, [])
        self.assertEqual(review.general_comments, [
            {
                'issue_opened': True,
                'rich_text': True,
                'text': (
                    "1 test failed:\n"
                    "\n"
                    "```"
                    "---- tests::test1 stdout ----\n"
                    "thread 'main' panicked at 'assertion failed: "
                    "`(left == right)`\n"
                    "  left: `1`,\n"
                    " right: `2`', tests/test.rs:4:9\n"
                    "line 1\n"
                    "line 2\n"
                    "line 3\n"
                    "line 4\n"
                    "line 5\n"
                    "line 6\n"
                    "line 7\n"
                    "line 8\n"
                    "line 9\n"
                    "line 10\n"
                    "line 11\n"
                    "line 12\n"
                    "line 13\n"
                    "line 14\n"
                    "line 15\n"
                    "line 16\n"
                    "line 17\n"
                    "line 18\n"
                    "line 19\n"
                    "line 20\n"
                    "line 21\n"
                    "line 22\n"
                    "line 23\n"
                    "line 24\n"
                    "line 25\n"
                    "line 26\n"
                    "line 27\n"
                    "line 28\n"
                    "line 29\n"
                    "line 30\n"
                    "line 31\n"
                    "line 32\n"
                    "line 33\n"
                    "line 34\n"
                    "line 35\n"
                    "line 36\n"
                    "line 37\n"
                    "line 38\n"
                    "line 39\n"
                    "line 40\n"
                    "line 41\n"
                    "line 42\n"
                    "line 43\n"
                    "line 44\n"
                    "line 45\n"
                    "line 46\n"
                    "line 47\n"
                    "line 48\n"
                    "line 49\n"
                    "line 50\n"
                    "line 51\n"
                    "line 52\n"
                    "line 53\n"
                    "line 54\n"
                    "line 55\n"
                    "line 56\n"
                    "line 57\n"
                    "line 58\n"
                    "line 59\n"
                    "line 60\n"
                    "line 61\n"
                    "line 62\n"
                    "line 63\n"
                    "line 64\n"
                    "line 65\n"
                    "line 66\n"
                    "line 67\n"
                    "line 68\n"
                    "line 69\n"
                    "line 70\n"
                    "line 71\n"
                    "line 72\n"
                    "line 73\n"
                    "line 74\n"
                    "line 75\n"
                    "line 76\n"
                    "line 77\n"
                    "line 78\n"
                    "line 79\n"
                    "line 80\n"
                    "line 81\n"
                    "line 82\n"
                    "line 83\n"
                    "line 84\n"
                    "line 85\n"
                    "line 86\n"
                    "line 87\n"
                    "line 88\n"
                    "line 89\n"
                    "line 90\n"
                    "line 91\n"
                    "line 92\n"
                    "line 93\n"
                    "line 94\n"
                    "line 95\n"
                    "line 96\n"
                    "<108 lines removed>"
                    "```"
                )
            },
        ])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                '-q',
                'test',
                '--',
                '--test-threads=1',
            ],
            with_errors=True,
            ignore_errors=True)

    @integration_test()
    @simulation_test(output=[
        'error: this file contains an unclosed delimiter\n',
        ' --> tests/test.rs:9:7\n',
        '  |\n',
        '1 | mod tests {\n',
        '  |           - unclosed delimiter\n',
        '2 |     #[test]\n',
        '3 |     fn test1() {\n',
        '  |                - unclosed delimiter\n',
        '...\n',
        '9 |     }\n',
        '  |       ^\n',
        '\n',
        'error: expected one of `.`, `;`, `?`, `}`, or an operator, found '
        '`#`\n',
        ' --> tests/test.rs:6:5\n',
        '  |\n',
        '1 | mod tests {\n',
        '  |           - unclosed delimiter\n',
        '...\n',
        '4 |         assert_eq!(1, 2)\n',
        '  |                         -\n',
        '  |                         |\n',
        '  |                         expected one of `.`, `;`, `?`, `}`, or '
        'an operator\n',
        '  |                         help: `}` may belong here\n',
        '5 |\n',
        '6 |     #[test]\n',
        '  |     ^ unexpected token\n',
        '\n',
        'error: aborting due to 2 previous errors\n',
        '\n',
        'error: could not compile `test`\n',
        '\n',
        'To learn more, run the command again with --verbose.\n',
        'error: build failed\n',
    ])
    def test_execute_with_test_true_syntax_errors(self):
        """Testing CargoTool.execute with test=True and syntax errors"""
        review, review_files = self.run_tool_execute(
            checkout_dir=self.checkout_dir,
            filename='main.rs',
            file_contents=self.GOOD_RS_CODE1,
            other_files={
                'main2.rs': self.GOOD_RS_CODE2,
                'tests/test.rs': self.BAD_RS_TESTS_SYNTAX_ERROR,
            },
            tool_settings={
                'test': True,
            })

        self.assertEqual(review.comments, [])
        self.assertEqual(review.general_comments, [
            {
                'issue_opened': True,
                'rich_text': True,
                'text': (
                    'One or more files contained compiler errors. For '
                    'details, run `cargo test` locally, or enable Clippy '
                    'support in Review Bot.'
                )
            },
        ])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                '-q',
                'test',
                '--',
                '--test-threads=1',
            ],
            with_errors=True,
            ignore_errors=True)

    @integration_test()
    @simulation_test(output=[
        json.dumps({
            'message': {
                'code': None,
                'level': 'error',
                'message': 'this file contains an unclosed delimiter',
                'spans': [
                    {
                        'column_end': 12,
                        'column_start': 11,
                        'line_end': 1,
                        'line_start': 1,
                        'is_primary': False,
                    },
                    {
                        'column_end': 17,
                        'column_start': 16,
                        'line_end': 3,
                        'line_start': 3,
                        'is_primary': False,
                    },
                    {
                        'column_end': 7,
                        'column_start': 7,
                        'line_end': 9,
                        'line_start': 9,
                        'is_primary': True,
                    },
                ],
            },
            'reason': 'compiler-message',
            'target': {
                'name': 'test',
                'src_path': '%(checkout_dir)s/tests/test.rs',
            },
        }),
        '\n',
        json.dumps({
            'message': {
                'code': None,
                'level': 'error',
                'message': 'expected `;`, found `#`',
                'spans': [
                    {
                        'column_end': 6,
                        'column_start': 5,
                        'line_end': 6,
                        'line_start': 6,
                        'is_primary': False,
                    },
                    {
                        'column_end': 25,
                        'column_start': 25,
                        'line_end': 4,
                        'line_start': 4,
                        'is_primary': True,
                    },
              ],
            },
            'reason': 'compiler-message',
            'target': {
                'name': 'test',
                'src_path': '%(checkout_dir)s/tests/test.rs',
            },
        }),
        '\n',
        json.dumps({
            'message': {
                'code': None,
                'level': 'error',
                'message': 'aborting due to 2 previous errors',
                'spans': [],
            },
            'reason': 'compiler-message',
            'target': {
                'name': 'test',
                'src_path': '%(checkout_dir)s/tests/test.rs',
            },
        }),
        '\n',
        json.dumps({
            'reason': 'build-finished',
            'success': False,
        }),
    ])
    def test_execute_with_test_clippy_true_syntax_errors(self):
        """Testing CargoTool.execute with test=True clippy=True and syntax
        errors
        """
        review, review_files = self.run_tool_execute(
            checkout_dir=self.checkout_dir,
            filename='main.rs',
            file_contents=self.GOOD_RS_CODE1,
            other_files={
                'main2.rs': self.GOOD_RS_CODE2,
                'tests/test.rs': self.BAD_RS_TESTS_SYNTAX_ERROR,
            },
            tool_settings={
                'clippy': True,
                'test': True,
            })

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_files['tests/test.rs'].id,
                'first_line': 1,
                'num_lines': 1,
                'text': (
                    'this file contains an unclosed delimiter\n'
                    '\n'
                    'Column: 11\n'
                    'Severity: error'
                ),
                'issue_opened': True,
                'rich_text': True,
            },
            {
                'filediff_id': review_files['tests/test.rs'].id,
                'first_line': 6,
                'num_lines': 1,
                'text': (
                    'expected `;`, found `#`\n'
                    '\n'
                    'Column: 5\n'
                    'Severity: error'
                ),
                'issue_opened': True,
                'rich_text': True,
            },
        ])
        self.assertEqual(review.general_comments, [])

        self.assertSpyCallCount(execute, 1)
        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                'clippy',
                '-q',
                '--message-format=json',
                '--tests',
            ],
            split_lines=True,
            with_errors=False,
            ignore_errors=True)

    def setup_simulation_test(self, output):
        """Set up the simulation test for cargotool.

        This will spy on :py:func:`~reviewbot.utils.process.execute`, making
        it return the provided data.

        Args:
            output (unicode):
                The outputted data.
        """
        output = [
            line % {
                'checkout_dir': self.checkout_dir,
            }
            for line in output
        ]

        # cargo clippy invocation expects a list of strings.
        #
        # cargo test expects a single string.
        self.spy_on(execute, op=kgb.SpyOpMatchAny([
            {
                'kwargs': {
                    'split_lines': True,
                },
                'call_fake': lambda *args, **kwargs: output,
            },
            {
                'kwargs': {
                    'split_lines': False,
                },
                'call_fake': lambda *args, **kwargs: ''.join(output),
            },
        ]))
