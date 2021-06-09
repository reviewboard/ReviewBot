"""Unit tests for reviewbot.tools.gotool."""

from __future__ import unicode_literals

import os
import shutil
import tempfile

import six

from reviewbot.tools.gotool import GoTool
from reviewbot.tools.testing import (BaseToolTestCase,
                                     ToolTestCaseMetaclass,
                                     integration_test,
                                     simulation_test)
from reviewbot.utils.process import execute


@six.add_metaclass(ToolTestCaseMetaclass)
class GoToolTests(BaseToolTestCase):
    """Unit tests for reviewbot.tools.gotool.GoTool."""

    tool_class = GoTool
    tool_exe_config_key = 'go'
    tool_exe_path = '/path/to/go'

    SAMPLE_GO_CODE = (
        b'package mypackage\n'
        b'\n'
        b'import (\n'
        b'\t"fmt"\n'
        b'\t"net/http"\n'
        b')\n'
        b'\n'
        b'func main() {\n'
        b'\ti := 100\n'
        b'\ti = i\n'
        b'\n'
        b'\tfmt.Println(main == nil)\n'
        b'\n'
        b'\tres, err := http.Get("https://www.reviewboard.org/")\n'
        b'\tdefer res.Body.Close()\n'
        b'\tfmt.Println(err)\n'
        b'}\n'
    )

    SAMPLE_SYNTAX_ERROR_GO_CODE = (
        b'package mypackage\n'
        b'\n'
        b'func main() {\n'
    )

    SAMPLE_TEST_CODE = (
        'package mypackage_test\n'
        '\n'
        'import (\n'
        '\t"testing"\n'
        ')\n'
        '\n'
        'func TestThingie(t *testing.T) {\n'
        '\tt.Errorf("Fail!", 123)\n'
        '}\n'
        '\n'
        'func TestOtherThingie(t *testing.T) {\n'
        '}\n'
    )

    def setUp(self):
        super(GoToolTests, self).setUp()

        self.checkout_dir = tempfile.mkdtemp()

        self.module_dir = os.path.join(self.checkout_dir, 'mypackage')
        os.mkdir(self.module_dir, 0o755)

        with open(os.path.join(self.checkout_dir, 'go.mod'), 'w') as fp:
            fp.write('module example.com/myrepo\n'
                     '\n'
                     'go 1.15\n')

    def tearDown(self):
        super(GoToolTests, self).tearDown()

        shutil.rmtree(self.checkout_dir)

    @integration_test()
    @simulation_test(test_output=[
        '{"Time":"2021-04-02T19:21:21.727302-07:00","Action":"run",'
        '"Package":"example.com/myrepo/mypackage","Test":"TestThingie"}\n',

        '{"Time":"2021-04-02T19:21:21.730586-07:00","Action":"output",'
        '"Package":"example.com/myrepo/mypackage","Test":"TestThingie",'
        '"Output":"=== RUN   TestThingie\\n"}\n',

        '{"Time":"2021-04-02T19:21:21.730671-07:00","Action":"output",'
        '"Package":"example.com/myrepo/mypackage","Test":"TestThingie",'
        '"Output":"    test_test.go:8: Fail!%!(EXTRA int=123)\\n"}\n',

        '{"Time":"2021-04-02T19:21:21.730701-07:00","Action":"output",'
        '"Package":"example.com/myrepo/mypackage","Test":"TestThingie",'
        '"Output":"--- FAIL: TestThingie (0.00s)\\n"}\n',

        '{"Time":"2021-04-02T19:21:21.730711-07:00","Action":"fail",'
        '"Package":"example.com/myrepo/mypackage","Test":"TestThingie",'
        '"Elapsed":0}\n',

        '{"Time":"2021-04-02T19:21:21.730725-07:00","Action":"run",'
        '"Package":"example.com/myrepo/mypackage",'
        '"Test":"TestOtherThingie"}\n',

        '{"Time":"2021-04-02T19:21:21.731042-07:00","Action":"output",'
        '"Package":"example.com/myrepo/mypackage","Test":"TestOtherThingie",'
        '"Output":"=== RUN   TestOtherThingie\\n"}\n',

        '{"Time":"2021-04-02T19:21:21.731074-07:00","Action":"output",'
        '"Package":"example.com/myrepo/mypackage","Test":"TestOtherThingie",'
        '"Output":"--- PASS: TestOtherThingie (0.00s)\\n"}\n',

        '{"Time":"2021-04-02T19:21:21.731085-07:00","Action":"pass",'
        '"Package":"example.com/myrepo/mypackage","Test":"TestOtherThingie",'
        '"Elapsed":0}\n',

        '{"Time":"2021-04-02T19:21:21.731091-07:00","Action":"output",'
        '"Package":"example.com/myrepo/mypackage","Output":"FAIL\\n"}\n',

        '{"Time":"2021-04-02T19:21:21.731162-07:00","Action":"output",'
        '"Package":"example.com/myrepo/mypackage",'
        '"Output":"FAIL\\texample.com/myrepo/mypackage\\t0.027s\\n"}\n',

        '{"Time":"2021-04-02T19:21:21.731174-07:00","Action":"fail",'
        '"Package":"example.com/myrepo/mypackage","Elapsed":0.027}\n',
    ])
    def test_execute_with_test(self):
        """Testing GoTool.execute with test setting"""
        with open(os.path.join(self.module_dir, 'test_test.go'), 'w') as fp:
            fp.write(self.SAMPLE_TEST_CODE)

        review, review_file = self.run_tool_execute(
            checkout_dir=self.checkout_dir,
            filename='mypackage/main.go',
            file_contents=self.SAMPLE_GO_CODE,
            tool_settings={
                'test': True,
            })

        self.assertEqual(review.general_comments, [
            {
                'text': (
                    'TestThingie failed in the example.com/myrepo/mypackage '
                    'package:\n'
                    '\n'
                    '```=== RUN   TestThingie\n'
                    '    test_test.go:8: Fail!%!(EXTRA int=123)\n'
                    '--- FAIL: TestThingie (0.00s)```'
                ),
                'issue_opened': True,
                'rich_text': True,
            },
        ])
        self.assertEqual(review.comments, [])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                'test',
                '-json',
                '-vet=off',
                './mypackage',
            ],
            with_errors=True,
            ignore_errors=True)
        self.assertSpyCallCount(execute, 1)

    @integration_test()
    @simulation_test(test_output=[
        '# example.com/myrepo/mypackage\n',

        'mypackage/main.go:4:1: syntax error: unexpected EOF, expecting }\n',

        'FAIL\texample.com/myrepo/mypackage [build failed]\n',
    ])
    def test_execute_with_test_and_syntax_error(self):
        """Testing GoTool.execute with test setting and syntax error"""
        with open(os.path.join(self.module_dir, 'test_test.go'), 'w') as fp:
            fp.write(self.SAMPLE_TEST_CODE)

        review, review_file = self.run_tool_execute(
            checkout_dir=self.checkout_dir,
            filename='mypackage/main.go',
            file_contents=self.SAMPLE_SYNTAX_ERROR_GO_CODE,
            tool_settings={
                'test': True,
            })

        self.assertEqual(review.general_comments, [
            {
                'text': (
                    'Unable to run `go test` on the mypackage package:\n'
                    '\n'
                    '```# example.com/myrepo/mypackage\n'
                    'mypackage/main.go:4:1: syntax error: unexpected EOF, '
                    'expecting }\n'
                    'FAIL\texample.com/myrepo/mypackage [build failed]```'
                ),
                'issue_opened': True,
                'rich_text': True,
            },
        ])
        self.assertEqual(review.comments, [])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                'test',
                '-json',
                '-vet=off',
                './mypackage',
            ],
            with_errors=True,
            ignore_errors=True)
        self.assertSpyCallCount(execute, 1)

    @integration_test()
    @simulation_test(vet_output=(
        "# example.com/myrepo/mypackage\n"

        "mypackage/main.go:10:2: self-assignment of i to i\n"

        "mypackage/main.go:15:8: using res before checking for errors\n"

        "mypackage/main.go:12:14: comparison of function main == nil is "
        "always false\n"
    ))
    def test_execute_with_vet(self):
        """Testing GoTool.execute with vet setting"""
        review, review_file = self.run_tool_execute(
            checkout_dir=self.checkout_dir,
            filename='mypackage/main.go',
            file_contents=self.SAMPLE_GO_CODE,
            tool_settings={
                'vet': True,
            })

        self.assertEqual(review.general_comments, [])
        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 10,
                'num_lines': 1,
                'text': (
                    'self-assignment of i to i\n'
                    '\n'
                    'Column: 2'
                ),
                'issue_opened': True,
                'rich_text': False,
            },
            {
                'filediff_id': review_file.id,
                'first_line': 15,
                'num_lines': 1,
                'text': (
                    'using res before checking for errors\n'
                    '\n'
                    'Column: 8'
                ),
                'issue_opened': True,
                'rich_text': False,
            },
            {
                'filediff_id': review_file.id,
                'first_line': 12,
                'num_lines': 1,
                'text': (
                    'comparison of function main == nil is always false\n'
                    '\n'
                    'Column: 14'
                ),
                'issue_opened': True,
                'rich_text': False,
            },
        ])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                'vet',
                './mypackage',
            ],
            with_errors=True,
            ignore_errors=True)
        self.assertSpyCallCount(execute, 1)

    @integration_test()
    @simulation_test(vet_output=(
        "# example.com/myrepo/mypackage\n"

        "vet: mypackage/main.go:3:15: expected '}', found 'EOF'\n"
    ))
    def test_execute_with_vet_and_syntax_error(self):
        """Testing GoTool.execute with vet setting and syntax error"""
        review, review_file = self.run_tool_execute(
            checkout_dir=self.checkout_dir,
            filename='mypackage/main.go',
            file_contents=self.SAMPLE_SYNTAX_ERROR_GO_CODE,
            tool_settings={
                'vet': True,
            })

        self.assertEqual(review.general_comments, [])
        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 3,
                'num_lines': 1,
                'text': (
                    "expected '}', found 'EOF'\n"
                    "\n"
                    "Column: 15"
                ),
                'issue_opened': True,
                'rich_text': False,
            },
        ])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                'vet',
                './mypackage',
            ],
            with_errors=True,
            ignore_errors=True)
        self.assertSpyCallCount(execute, 1)

    @integration_test()
    @simulation_test(
        test_output=[
            '{"Time":"2021-04-02T19:21:21.727302-07:00","Action":"run",'
            '"Package":"example.com/myrepo/mypackage","Test":"TestThingie"}\n',

            '{"Time":"2021-04-02T19:21:21.730586-07:00","Action":"output",'
            '"Package":"example.com/myrepo/mypackage","Test":"TestThingie",'
            '"Output":"=== RUN   TestThingie\\n"}\n',

            '{"Time":"2021-04-02T19:21:21.730671-07:00","Action":"output",'
            '"Package":"example.com/myrepo/mypackage","Test":"TestThingie",'
            '"Output":"    test_test.go:8: Fail!%!(EXTRA int=123)\\n"}\n',

            '{"Time":"2021-04-02T19:21:21.730701-07:00","Action":"output",'
            '"Package":"example.com/myrepo/mypackage","Test":"TestThingie",'
            '"Output":"--- FAIL: TestThingie (0.00s)\\n"}\n',

            '{"Time":"2021-04-02T19:21:21.730711-07:00","Action":"fail",'
            '"Package":"example.com/myrepo/mypackage","Test":"TestThingie",'
            '"Elapsed":0}\n',

            '{"Time":"2021-04-02T19:21:21.730725-07:00","Action":"run",'
            '"Package":"example.com/myrepo/mypackage",'
            '"Test":"TestOtherThingie"}\n',

            '{"Time":"2021-04-02T19:21:21.731042-07:00","Action":"output",'
            '"Package":"example.com/myrepo/mypackage",'
            '"Test":"TestOtherThingie",'
            '"Output":"=== RUN   TestOtherThingie\\n"}\n',

            '{"Time":"2021-04-02T19:21:21.731074-07:00","Action":"output",'
            '"Package":"example.com/myrepo/mypackage",'
            '"Test":"TestOtherThingie",'
            '"Output":"--- PASS: TestOtherThingie (0.00s)\\n"}\n',

            '{"Time":"2021-04-02T19:21:21.731085-07:00","Action":"pass",'
            '"Package":"example.com/myrepo/mypackage",'
            '"Test":"TestOtherThingie",'
            '"Elapsed":0}\n',

            '{"Time":"2021-04-02T19:21:21.731091-07:00","Action":"output",'
            '"Package":"example.com/myrepo/mypackage","Output":"FAIL\\n"}\n',

            '{"Time":"2021-04-02T19:21:21.731162-07:00","Action":"output",'
            '"Package":"example.com/myrepo/mypackage",'
            '"Output":"FAIL\\texample.com/myrepo/mypackage\\t0.027s\\n"}\n',

            '{"Time":"2021-04-02T19:21:21.731174-07:00","Action":"fail",'
            '"Package":"example.com/myrepo/mypackage","Elapsed":0.027}\n',
        ],
        vet_output=(
            "# example.com/myrepo/mypackage\n"

            "mypackage/main.go:10:2: self-assignment of i to i\n"

            "mypackage/main.go:15:8: using res before checking for errors\n"

            "mypackage/main.go:12:14: comparison of function main == nil is "
            "always false\n"
        )
    )
    def test_execute_with_test_and_vet(self):
        """Testing GoTool.execute with test and vet settings"""
        with open(os.path.join(self.module_dir, 'test_test.go'), 'w') as fp:
            fp.write(self.SAMPLE_TEST_CODE)

        review, review_file = self.run_tool_execute(
            checkout_dir=self.checkout_dir,
            filename='mypackage/main.go',
            file_contents=self.SAMPLE_GO_CODE,
            tool_settings={
                'test': True,
                'vet': True,
            })

        self.assertEqual(review.general_comments, [
            {
                'text': (
                    'TestThingie failed in the example.com/myrepo/mypackage '
                    'package:\n'
                    '\n'
                    '```=== RUN   TestThingie\n'
                    '    test_test.go:8: Fail!%!(EXTRA int=123)\n'
                    '--- FAIL: TestThingie (0.00s)```'
                ),
                'issue_opened': True,
                'rich_text': True,
            },
        ])
        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 10,
                'num_lines': 1,
                'text': (
                    'self-assignment of i to i\n'
                    '\n'
                    'Column: 2'
                ),
                'issue_opened': True,
                'rich_text': False,
            },
            {
                'filediff_id': review_file.id,
                'first_line': 15,
                'num_lines': 1,
                'text': (
                    'using res before checking for errors\n'
                    '\n'
                    'Column: 8'
                ),
                'issue_opened': True,
                'rich_text': False,
            },
            {
                'filediff_id': review_file.id,
                'first_line': 12,
                'num_lines': 1,
                'text': (
                    'comparison of function main == nil is always false\n'
                    '\n'
                    'Column: 14'
                ),
                'issue_opened': True,
                'rich_text': False,
            },
        ])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                'test',
                '-json',
                '-vet=off',
                './mypackage',
            ],
            with_errors=True,
            ignore_errors=True)
        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                'vet',
                './mypackage',
            ],
            with_errors=True,
            ignore_errors=True)
        self.assertSpyCallCount(execute, 2)

    @integration_test()
    @simulation_test(
        test_output=[
            '{"Time":"2021-04-02T22:58:40.97741-07:00","Action":"run",'
            '"Package":"example.com/myrepo/mypackage","Test":"TestThingie"}\n',

            '{"Time":"2021-04-02T22:58:40.978702-07:00","Action":"output",'
            '"Package":"example.com/myrepo/mypackage","Test":"TestThingie",'
            '"Output":"=== RUN   TestThingie\\n"}\n',

            '{"Time":"2021-04-02T22:58:40.978734-07:00","Action":"output",'
            '"Package":"example.com/myrepo/mypackage","Test":"TestThingie",'
            '"Output":"--- PASS: TestThingie (0.00s)\\n"}\n',

            '{"Time":"2021-04-02T22:58:40.97874-07:00","Action":"pass",'
            '"Package":"example.com/myrepo/mypackage","Test":"TestThingie",'
            '"Elapsed":0}\n',

            '{"Time":"2021-04-02T22:58:40.978754-07:00","Action":"output",'
            '"Package":"example.com/myrepo/mypackage","Output":"PASS\\n"}\n',

            '{"Time":"2021-04-02T22:58:40.978791-07:00","Action":"output",'
            '"Package":"example.com/myrepo/mypackage",'
            '"Output":"ok  \\texample.com/myrepo/mypackage\\t0.007s\\n"}\n',

            '{"Time":"2021-04-02T22:58:40.980595-07:00","Action":"pass",'
            '"Package":"example.com/myrepo/mypackage","Elapsed":0.008}\n',
        ],
        vet_output=''
    )
    def test_execute_with_test_and_vet_and_success(self):
        """Testing GoTool.execute with test and vet settings and success"""
        with open(os.path.join(self.module_dir, 'test_test.go'), 'w') as fp:
            fp.write('package mypackage_test\n'
                     '\n'
                     'import (\n'
                     '\t"testing"\n'
                     ')\n'
                     '\n'
                     'func TestThingie(t *testing.T) {\n'
                     '}\n')

        review, review_file = self.run_tool_execute(
            checkout_dir=self.checkout_dir,
            filename='mypackage/main.go',
            file_contents=(
                b'package mypackage\n'
                b'\n'
                b'func main() {\n'
                b'}\n'
            ),
            tool_settings={
                'test': True,
                'vet': True,
            })

        self.assertEqual(review.general_comments, [])
        self.assertEqual(review.comments, [])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                'test',
                '-json',
                '-vet=off',
                './mypackage',
            ],
            with_errors=True,
            ignore_errors=True)
        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                'vet',
                './mypackage',
            ],
            with_errors=True,
            ignore_errors=True)
        self.assertSpyCallCount(execute, 2)

    def setup_simulation_test(self, test_output=[], vet_output=''):
        """Set up the simulation test for GoTool.

        This will spy on :py:func:`~reviewbot.utils.process.execute`, making
        it return the provided output.

        Args:
            test_output (list of unicode, optional):
                The outputted content from :command:`go test`.

            vet_output (unicode, optional):
                The outputted content from :command:`go vet`.
        """
        @self.spy_for(execute)
        def _execute(cmdline, **kwargs):
            if cmdline[1] == 'test':
                return test_output
            elif cmdline[1] == 'vet':
                return vet_output
            else:
                assert False
