"""Unit tests for reviewbot.tools.clang."""

from __future__ import unicode_literals

import os

try:
    # Python 3.x
    from plistlib import writePlist as dump_plist
except ImportError:
    # Python 2.7
    from plistlib import dump as dump_plist

import six

from reviewbot.tools.clang import ClangTool
from reviewbot.tools.testing import (BaseToolTestCase,
                                     ToolTestCaseMetaclass,
                                     integration_test,
                                     simulation_test)
from reviewbot.utils.filesystem import tmpfiles
from reviewbot.utils.process import execute


@six.add_metaclass(ToolTestCaseMetaclass)
class ClangToolTests(BaseToolTestCase):
    """Unit tests for reviewbot.tools.clang.ClangTool."""

    tool_class = ClangTool
    tool_exe_config_key = 'clang'
    tool_exe_path = '/path/to/clang'

    @integration_test()
    @simulation_test(plist_data={
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
    def test_execute_with_c(self):
        """Testing ClangTool.execute with C file"""
        review, review_file = self.run_tool_execute(
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
                self.tool_exe_path,
                '-S',
                '--analyze',
                '-Xanalyzer',
                '-analyzer-output=plist',
                'test.c',
                '-o',
                tmpfiles[-1],
            ],
            ignore_errors=True)

    @integration_test()
    @simulation_test(plist_data={
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
    def test_execute_with_objc(self):
        """Testing ClangTool.execute with ObjC file"""
        review, review_file = self.run_tool_execute(
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
                self.tool_exe_path,
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

    @integration_test()
    @simulation_test(output=(
        "test.m:3:6: error: use of undeclared identifier 'badcode'\n"
        "    {badcode}\n"
        "     ^\n"
        "1 error generated.\n"
    ))
    def test_execute_with_objc_and_compiler_error(self):
        """Testing ClangTool.execute with ObjC file and compiler error"""
        review, review_file = self.run_tool_execute(
            filename='test.m',
            file_contents=(
                b'int main()\n'
                b'{\n'
                b'    {badcode}\n'
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
                    "    {badcode}\n"
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
                self.tool_exe_path,
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

    @integration_test()
    @simulation_test(plist_data={
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
    def test_execute_with_objcpp(self):
        """Testing ClangTool.execute with ObjC++ file"""
        review, review_file = self.run_tool_execute(
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
                self.tool_exe_path,
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

    @integration_test()
    @simulation_test(output=(
        "test.mm:5:6: error: use of undeclared identifier 'badcode'\n"
        "    {badcode}\n"
        "     ^\n"
        "1 error generated.\n"
    ))
    def test_execute_with_objcpp_and_compiler_error(self):
        """Testing ClangTool.execute with ObjC++ file and compiler error"""
        review, review_file = self.run_tool_execute(
            filename='test.mm',
            file_contents=(
                b'class Foo {};\n'
                b'\n'
                b'int main()\n'
                b'{\n'
                b'    {badcode}\n'
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
                    "    {badcode}\n"
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
                self.tool_exe_path,
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

    @integration_test()
    @simulation_test(plist_data={
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
                'description': (
                    "Value stored to 'i' during its initialization is "
                    "never read"
                ),
                'location': {
                    'col': 13,
                    'line': 7,
                    'file': 0,
                },
                'path': [
                    {
                        'kind': 'event',
                        'ranges': [
                            [
                                {
                                    'col': 9,
                                    'file': 0,
                                    'line': 7,
                                },
                                {
                                    'col': 9,
                                    'file': 0,
                                    'line': 7,
                                },
                            ],
                            [
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
                            ],
                        ],
                    },
                ],
            },
        ],
    })
    def test_execute_with_cmdline_args(self):
        """Testing ClangTool.execute with cmdline_args setting"""
        review, review_file = self.run_tool_execute(
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
                self.tool_exe_path,
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

    def setup_simulation_test(self, plist_data=None, output=None):
        """Set up the simulation test for Clang.

        This will spy on :py:func:`~reviewbot.utils.process.execute`, making
        it write a plist file, if data is provided, or delete it if simulating
        a compiler error.

        Args:
            plist_data (dict, optional):
                The simulated plist data, if simulating a successful run.

            output (unicode, optional):
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
