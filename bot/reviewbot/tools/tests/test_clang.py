"""Unit tests for reviewbot.tools.clang."""

from __future__ import unicode_literals

import os
import tempfile
from unittest import SkipTest

try:
    # Python 3.x
    from plistlib import writePlist as dump_plist
except ImportError:
    # Python 2.7
    from plistlib import dump as dump_plist

import kgb

from reviewbot.config import config
from reviewbot.repositories import GitRepository
from reviewbot.testing import TestCase
from reviewbot.tools.clang import ClangTool
from reviewbot.utils.filesystem import tmpfiles
from reviewbot.utils.process import execute


class BaseClangToolTests(kgb.SpyAgency, TestCase):
    """Base class for clang unit tests."""

    clang_path = None

    def check_execute_with_c(self):
        """Common tests for execute with a C file."""
        review, review_file = self._run_execute(
            filename='test.c',
            file_contents=(
                b'int main()\n'
                b'{\n'
                b'    void (*foo)(void);\n'
                b'    foo = 0;\n'
                b'    foo();\n'
                b'\n'
                b'    int i = (1 /\n'
                b'             0);\n'
                b'}\n'
            ))

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 5,
                'num_lines': 1,
                'text': (
                    'Called function pointer is null (null dereference)\n'
                    '\n'
                    'Column: 5'
                ),
                'issue_opened': True,
                'rich_text': False,
            },
            {
                'filediff_id': review_file.id,
                'first_line': 7,
                'num_lines': 2,
                'text': (
                    "Value stored to 'i' during its initialization is "
                    "never read\n"
                    "\n"
                    "Column: 9"
                ),
                'issue_opened': True,
                'rich_text': False,
            },
        ])

        self.assertSpyCalledWith(
            execute,
            [
                self.clang_path,
                '-S',
                '--analyze',
                '-Xanalyzer',
                '-analyzer-output=plist',
                'test.c',
                '-o',
                tmpfiles[-1],
            ],
            ignore_errors=True)

    def check_execute_with_objc(self):
        """Common tests for execute with an ObjC file"""
        review, review_file = self._run_execute(
            filename='test.m',
            file_contents=(
                b'int main()\n'
                b'{\n'
                b'    @autoreleasepool {\n'
                b'        int i = 1 / 0;\n'
                b'    }\n'
                b'\n'
                b'    return 0;\n'
                b'}\n'
            ))

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 4,
                'num_lines': 1,
                'text': (
                    "Value stored to 'i' during its initialization is "
                    "never read\n"
                    "\n"
                    "Column: 13"
                ),
                'issue_opened': True,
                'rich_text': False,
            },
            {
                'filediff_id': review_file.id,
                'first_line': 4,
                'num_lines': 1,
                'text': (
                    'Division by zero\n'
                    '\n'
                    'Column: 17'
                ),
                'issue_opened': True,
                'rich_text': False,
            },
        ])

        self.assertSpyCalledWith(
            execute,
            [
                self.clang_path,
                '-S',
                '--analyze',
                '-Xanalyzer',
                '-analyzer-output=plist',
                '-ObjC',
                'test.m',
                '-o',
                tmpfiles[-1],
            ],
            ignore_errors=True)

    def check_execute_with_objc_and_compiler_error(self):
        """Common tests for execute with an ObjC file and compiler error."""
        review, review_file = self._run_execute(
            filename='test.m',
            file_contents=(
                b'int main()\n'
                b'{\n'
                b'    [badcode]\n'
                b'\n'
                b'    return 0;\n'
                b'}\n'
            ))

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 1,
                'num_lines': 1,
                'text': (
                    "Clang could not analyze this file, due to the "
                    "following errors:\n"
                    "\n"
                    "```\n"
                    "test.m:3:6: error: use of undeclared identifier "
                    "'badcode'\n"
                    "    [badcode]\n"
                    "     ^\n"
                    "1 error generated.\n"
                    "```"
                ),
                'issue_opened': True,
                'rich_text': True,
            },
        ])

        self.assertSpyCalledWith(
            execute,
            [
                self.clang_path,
                '-S',
                '--analyze',
                '-Xanalyzer',
                '-analyzer-output=plist',
                '-ObjC',
                'test.m',
                '-o',
                tmpfiles[-1],
            ],
            ignore_errors=True)

    def check_execute_with_objcpp(self):
        """Common tests for execute with an ObjC++ file."""
        review, review_file = self._run_execute(
            filename='test.mm',
            file_contents=(
                b'class Foo {};\n'
                b'\n'
                b'int main()\n'
                b'{\n'
                b'    @autoreleasepool {\n'
                b'        int i = 1 / 0;\n'
                b'    }\n'
                b'\n'
                b'    return 0;\n'
                b'}\n'
            ))

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 6,
                'num_lines': 1,
                'text': (
                    "Value stored to 'i' during its initialization is "
                    "never read\n"
                    "\n"
                    "Column: 13"
                ),
                'issue_opened': True,
                'rich_text': False,
            },
            {
                'filediff_id': review_file.id,
                'first_line': 6,
                'num_lines': 1,
                'text': (
                    'Division by zero\n'
                    '\n'
                    'Column: 17'
                ),
                'issue_opened': True,
                'rich_text': False,
            },
        ])

        self.assertSpyCalledWith(
            execute,
            [
                self.clang_path,
                '-S',
                '--analyze',
                '-Xanalyzer',
                '-analyzer-output=plist',
                '-ObjC++',
                'test.mm',
                '-o',
                tmpfiles[-1],
            ],
            ignore_errors=True)

    def check_execute_with_objcpp_and_compiler_error(self):
        """Common tests for execute with an ObjC++ file and compiler error."""
        review, review_file = self._run_execute(
            filename='test.mm',
            file_contents=(
                b'class Foo {};\n'
                b'\n'
                b'int main()\n'
                b'{\n'
                b'    [badcode]\n'
                b'\n'
                b'    return 0;\n'
                b'}\n'
            ))

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 1,
                'num_lines': 1,
                'text': (
                    "Clang could not analyze this file, due to the "
                    "following errors:\n"
                    "\n"
                    "```\n"
                    "test.mm:5:6: error: use of undeclared identifier "
                    "'badcode'\n"
                    "    [badcode]\n"
                    "     ^\n"
                    "1 error generated.\n"
                    "```"
                ),
                'issue_opened': True,
                'rich_text': True,
            },
        ])

        self.assertSpyCalledWith(
            execute,
            [
                self.clang_path,
                '-S',
                '--analyze',
                '-Xanalyzer',
                '-analyzer-output=plist',
                '-ObjC++',
                'test.mm',
                '-o',
                tmpfiles[-1],
            ],
            ignore_errors=True)

    def check_execute_with_cmdline_args(self):
        """Common tests for execute with the cmdline_args setting."""
        review, review_file = self._run_execute(
            filename='test.c',
            file_contents=(
                b'int main()\n'
                b'{\n'
                b'    void (*foo)(void);\n'
                b'    foo = 0;\n'
                b'    foo();\n'
                b'\n'
                b'    int i = (1 /\n'
                b'             0);\n'
                b'}\n'
            ),
            tool_settings={
                'cmdline_args': '-I/inc -W123',
            })

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 5,
                'num_lines': 1,
                'text': (
                    'Called function pointer is null (null dereference)\n'
                    '\n'
                    'Column: 5'
                ),
                'issue_opened': True,
                'rich_text': False,
            },
            {
                'filediff_id': review_file.id,
                'first_line': 7,
                'num_lines': 2,
                'text': (
                    "Value stored to 'i' during its initialization is never "
                    "read\n"
                    "\n"
                    "Column: 9"
                ),
                'issue_opened': True,
                'rich_text': False,
            },
        ])

        self.assertSpyCalledWith(
            execute,
            [
                config['exe_paths']['clang'],
                '-S',
                '--analyze',
                '-Xanalyzer',
                '-analyzer-output=plist',
                '-I/inc',
                '-W123',
                'test.c',
                '-o',
                tmpfiles[-1],
            ],
            ignore_errors=True)

    def _run_execute(self, filename, file_contents=None, tool_settings={}):
        """Run execute with the given file and settings.

        This will create the review objects, set up a repository, apply any
        configuration, and run
        :py:meth:`~reviewbot.tools.clang.ClangTool.execute`.

        Args:
            filename (unicode):
                The filename of the file being reviewed.

            file_contents (bytes, optional):
                File content to review.

            tool_settings (dict, optional):
                The settings to pass to
                :py:class:`~reviewbot.tools.clang.ClangTool`.

        Returns:
            tuple:
            A tuple containing the review and the file.
        """
        repository = GitRepository(name='MyRepo',
                                   clone_path='git://example.com/repo')
        self.spy_on(repository.sync, call_original=False)

        @self.spy_for(repository.checkout)
        def _checkout(_self, *args, **kwargs):
            return tempfile.mkdtemp()

        review = self.create_review()
        review_file = self.create_review_file(
            review,
            source_file=filename,
            dest_file=filename,
            diff_data=self.create_diff_data(chunks=[{
                'change': 'insert',
                'lines': file_contents.splitlines(),
                'new_linenum': 1,
            }]),
            patched_content=file_contents)

        worker_config = {
            'exe_paths': {
                'clang': self.clang_path,
            },
        }

        with self.override_config(worker_config):
            tool = ClangTool(settings=tool_settings)
            tool.execute(review,
                         repository=repository)

        return review, review_file


class ClangToolTests(BaseClangToolTests):
    """Unit tests for reviewbot.tools.clang.ClangTool."""

    clang_path = '/path/to/clang'

    def test_execute_with_c(self):
        """Testing ClangTool.execute with C file"""
        self.simulate_clang_result(
            plist_data={
                'files': ['test.c'],
                'diagnostics': [
                    {
                        'description': (
                            'Called function pointer is null (null '
                            'dereference)'
                        ),
                        'location': {
                            'col': 5,
                            'file': 0,
                            'line': 5,
                        },
                    },
                    {
                        'description': (
                            "Value stored to 'i' during its "
                            "initialization is never read"
                        ),
                        'location': {
                            'col': 9,
                            'file': 0,
                            'line': 7,
                        },
                        'path': [
                            {
                                'kind': 'event',
                                'ranges': [[
                                    {
                                        'col': 9,
                                        'file': 0,
                                        'line': 7,
                                    },
                                    {
                                        'col': 9,
                                        'file': 0,
                                        'line': 8,
                                    },
                                ]],
                            },
                        ],
                    },
                ],
            })

        self.check_execute_with_c()

    def test_execute_with_objc(self):
        """Testing ClangTool.execute with ObjC file"""
        self.simulate_clang_result(
            plist_data={
                'files': ['test.m'],
                'diagnostics': [
                    {
                        'description': (
                            "Value stored to 'i' during its initialization "
                            "is never read"
                        ),
                        'location': {
                            'col': 13,
                            'file': 0,
                            'line': 4,
                        },
                    },
                    {
                        'description': 'Division by zero',
                        'location': {
                            'col': 19,
                            'file': 0,
                            'line': 4,
                        },
                        'path': [
                            {
                                'kind': 'event',
                                'ranges': [[
                                    {
                                        'col': 17,
                                        'file': 0,
                                        'line': 4,
                                    },
                                    {
                                        'col': 21,
                                        'file': 0,
                                        'line': 4,
                                    },
                                ]],
                            },
                        ],
                    },
                ],
            })

        self.check_execute_with_objc()

    def test_execute_with_objc_and_compiler_error(self):
        """Testing ClangTool.execute with ObjC file and compiler error"""
        self.simulate_clang_result(output=(
            "test.m:3:6: error: use of undeclared identifier "
            "'badcode'\n"
            "    [badcode]\n"
            "     ^\n"
            "1 error generated.\n"
        ))

        self.check_execute_with_objc_and_compiler_error()

    def test_execute_with_objcpp(self):
        """Testing ClangTool.execute with ObjC++ file"""
        self.simulate_clang_result(plist_data={
            'files': ['test.mm'],
            'diagnostics': [
                {
                    'description': (
                        "Value stored to 'i' during its initialization "
                        "is never read"
                    ),
                    'location': {
                        'col': 13,
                        'file': 0,
                        'line': 6,
                    },
                },
                {
                    'description': 'Division by zero',
                    'location': {
                        'col': 19,
                        'file': 0,
                        'line': 6,
                    },
                    'path': [
                        {
                            'kind': 'event',
                            'ranges': [[
                                {
                                    'col': 17,
                                    'file': 0,
                                    'line': 6,
                                },
                                {
                                    'col': 21,
                                    'file': 0,
                                    'line': 6,
                                },
                            ]],
                        },
                    ],
                },
            ],
        })

        self.check_execute_with_objcpp()

    def test_execute_with_objcpp_and_compiler_error(self):
        """Testing ClangTool.execute with ObjC++ file and compiler error"""
        self.simulate_clang_result(output=(
            "test.m:3:6: error: use of undeclared identifier "
            "'badcode'\n"
            "    [badcode]\n"
            "     ^\n"
            "1 error generated.\n"
        ))

        self.check_execute_with_objc_and_compiler_error()

    def test_execute_with_cmdline_args(self):
        """Testing ClangTool.execute with cmdline_args setting"""
        self.simulate_clang_result(plist_data={
            'files': ['test.c'],
            'diagnostics': [
                {
                    'description': (
                        'Called function pointer is null (null '
                        'dereference)'
                    ),
                    'location': {
                        'col': 5,
                        'line': 5,
                        'file': 0,
                    },
                },
                {
                    'description': 'Something terrible happened here',
                    'location': {
                        'col': 13,
                        'line': 7,
                        'file': 0,
                    },
                    'path': [
                        {
                            'kind': 'event',
                            'ranges': [[
                                {
                                    'col': 13,
                                    'file': 0,
                                    'line': 7,
                                },
                                {
                                    'col': 15,
                                    'file': 0,
                                    'line': 8,
                                },
                            ]],
                        },
                    ],
                },
            ],
        })

    def simulate_clang_result(self, plist_data=None, output=None):
        """Simulate a response from clang.

        This will spy on :py:func:`~reviewbot.utils.process.execute`, making
        it write a plist file, if data is provided, or delete it if simulating
        a compiler error.

        Compiler error text will also be returned.

        Args:
            plist_data (dict, optional):
                The simulated plist data, if simulating a successful run.

            output (unicode):
                The resulting compiler output, if simulating a compiler error.
        """
        @self.spy_for(execute)
        def _execute(cmdline, **kwargs):
            filename = cmdline[-1]

            if plist_data:
                with open(cmdline[-1], 'wb') as fp:
                    dump_plist(plist_data, fp)
            else:
                # clang will delete the output file if there's a compiler
                # error.
                os.unlink(filename)

            return output


class ClangToolIntegrationTests(BaseClangToolTests):
    """Integration tests for reviewbot.tools.clang.ClangTool."""

    preserve_path_env = True

    def setUp(self):
        super(ClangToolIntegrationTests, self).setUp()

        if not ClangTool().check_dependencies():
            raise SkipTest('Clang dependencies not available')

        self.clang_path = config['exe_paths']['clang']

        self.spy_on(execute)

    def test_execute_with_c(self):
        """Testing ClangTool.execute with clang binary and C file"""
        self.check_execute_with_c()

    def test_execute_with_objc(self):
        """Testing ClangTool.execute with clang binary and ObjC file"""
        self.check_execute_with_objc()

    def test_execute_with_objc_and_compiler_error(self):
        """Testing ClangTool.execute with clang binary and ObjC file and
        compiler error
        """
        self.check_execute_with_objc_and_compiler_error()

    def test_execute_with_objcpp(self):
        """Testing ClangTool.execute with clang binary and ObjC++ file"""
        self.check_execute_with_objcpp()

    def test_execute_with_objcpp_and_compiler_error(self):
        """Testing ClangTool.execute with clang binary and ObjC++ file and
        compiler error
        """
        self.check_execute_with_objcpp_and_compiler_error()

    def test_execute_with_cmdline_args(self):
        """Testing ClangTool.execute with clang binary and cmdline_args
        setting
        """
        self.check_execute_with_cmdline_args()
