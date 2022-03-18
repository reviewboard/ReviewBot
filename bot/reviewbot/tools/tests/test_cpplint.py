"""Unit tests for reviewbot.tools.cpplint."""

from __future__ import unicode_literals

import os

import kgb
import six

from reviewbot.tools.cpplint import CPPLintTool
from reviewbot.tools.testing import (BaseToolTestCase,
                                     ToolTestCaseMetaclass,
                                     integration_test,
                                     simulation_test)
from reviewbot.utils.filesystem import tmpdirs
from reviewbot.utils.process import execute


@six.add_metaclass(ToolTestCaseMetaclass)
class CPPLintToolTests(BaseToolTestCase):
    """Unit tests for reviewbot.tools.cpplint.CPPLintTool."""

    tool_class = CPPLintTool
    tool_exe_config_key = 'cpplint'
    tool_exe_path = '/path/to/cpplint'

    sample_cpp_code = (
        b'#include "a.h"\n'
        b'\n'
        b'using namespace foo;\n'
        b'\n'
        b'unsigned int main() {\n'
        b'    int i=0;  \n'
        b'\n'
        b'    return (int)1;\n'
        b'}\n'
    )

    @integration_test()
    @simulation_test(output=(
        '/path/to/test.cc:0:  No copyright message found.  You should have '
        'a line: "Copyright [year] <Copyright Owner>"  [legal/copyright] [5]\n'

        '/path/to/test.cc:3:  Do not use namespace using-directives.  Use '
        'using-declarations instead.  [build/namespaces] [5]\n'

        'Done processing /path/to/test.cc\n'

        'Total errors found: 2\n'
    ))
    def test_execute(self):
        """Testing CPPLintTool.execute"""
        review, review_file = self.run_tool_execute(
            filename='test.cc',
            file_contents=self.sample_cpp_code,
            tool_settings={
                'verbosity': 5,
            })

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 1,
                'num_lines': 1,
                'text': (
                    'No copyright message found.  You should have a line: '
                    '"Copyright [year] <Copyright Owner>"\n'
                    '\n'
                    'Error code: legal/copyright'
                ),
                'issue_opened': True,
                'rich_text': False,
            },
            {
                'filediff_id': review_file.id,
                'first_line': 3,
                'num_lines': 1,
                'text': (
                    'Do not use namespace using-directives.  Use '
                    'using-declarations instead.\n'
                    '\n'
                    'Error code: build/namespaces'
                ),
                'issue_opened': True,
                'rich_text': False,
            },
        ])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                '--verbose=5',
                os.path.join(tmpdirs[-1], 'test.cc'),
            ],
            ignore_errors=True)

    @integration_test()
    @simulation_test(output=(
        '/path/to/test.cc:3:  Do not use namespace using-directives.  Use '
        'using-declarations instead.  [build/namespaces] [5]\n'

        '/path/to/test.cc:8:  Using C-style cast.  Use static_cast<int>(...) '
        'instead  [readability/casting] [4]\n'

        'Done processing /path/to/test.cc\n'

        'Total errors found: 2\n'
    ))
    def test_execute_with_excluded_checks(self):
        """Testing CPPLintTool.execute with excluded_checks setting"""
        review, review_file = self.run_tool_execute(
            filename='test.cc',
            file_contents=self.sample_cpp_code,
            tool_settings={
                'excluded_checks': ('-legal/copyright,-whitespace,'
                                    '-build,+build/namespaces'),
                'verbosity': 1,
            })

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 3,
                'num_lines': 1,
                'text': (
                    'Do not use namespace using-directives.  Use '
                    'using-declarations instead.\n'
                    '\n'
                    'Error code: build/namespaces'
                ),
                'issue_opened': True,
                'rich_text': False,
            },
            {
                'filediff_id': review_file.id,
                'first_line': 8,
                'num_lines': 1,
                'text': (
                    'Using C-style cast.  Use static_cast<int>(...) instead\n'
                    '\n'
                    'Error code: readability/casting'
                ),
                'issue_opened': True,
                'rich_text': False,
            },
        ])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                '--verbose=1',
                ('--filter=-legal/copyright,-whitespace,-build,'
                 '+build/namespaces'),
                os.path.join(tmpdirs[-1], 'test.cc'),
            ],
            ignore_errors=True)

    @integration_test()
    @simulation_test(output=(
        '/path/to/test.cc:0:  No copyright message found.  You should have '
        'a line: "Copyright [year] <Copyright Owner>"  [legal/copyright] [5]\n'

        '/path/to/test.cc:1:  Include the directory when naming header files  '
        '[build/include_subdir] [4]\n'

        '/path/to/test.cc:3:  Do not use namespace using-directives.  Use '
        'using-declarations instead.  [build/namespaces] [5]\n'

        '/path/to/test.cc:6:  Line ends in whitespace.  Consider deleting '
        'these extra spaces.  [whitespace/end_of_line] [4]\n'

        '/path/to/test.cc:6:  Missing spaces around =  [whitespace/operators] '
        '[4]\n'

        '/path/to/test.cc:8:  Using C-style cast.  Use static_cast<int>(...) '
        'instead  [readability/casting] [4]\n'

        'Done processing /path/to/test.cc\n'

        'Total errors found: 6\n'
    ))
    def test_execute_with_verbosity(self):
        """Testing CPPLintTool.execute with verbosity setting"""
        review, review_file = self.run_tool_execute(
            filename='test.cc',
            file_contents=self.sample_cpp_code,
            tool_settings={
                'verbosity': 1,
            })

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 1,
                'num_lines': 1,
                'text': (
                    'No copyright message found.  You should have a line: '
                    '"Copyright [year] <Copyright Owner>"\n'
                    '\n'
                    'Error code: legal/copyright'
                ),
                'issue_opened': True,
                'rich_text': False,
            },
            {
                'filediff_id': review_file.id,
                'first_line': 1,
                'num_lines': 1,
                'text': (
                    'Include the directory when naming header files\n'
                    '\n'
                    'Error code: build/include_subdir'
                ),
                'issue_opened': True,
                'rich_text': False,
            },
            {
                'filediff_id': review_file.id,
                'first_line': 3,
                'num_lines': 1,
                'text': (
                    'Do not use namespace using-directives.  Use '
                    'using-declarations instead.\n'
                    '\n'
                    'Error code: build/namespaces'
                ),
                'issue_opened': True,
                'rich_text': False,
            },
            {
                'filediff_id': review_file.id,
                'first_line': 6,
                'num_lines': 1,
                'text': (
                    'Line ends in whitespace.  Consider deleting these '
                    'extra spaces.\n'
                    '\n'
                    'Error code: whitespace/end_of_line'
                ),
                'issue_opened': True,
                'rich_text': False,
            },
            {
                'filediff_id': review_file.id,
                'first_line': 6,
                'num_lines': 1,
                'text': (
                    'Missing spaces around =\n'
                    '\n'
                    'Error code: whitespace/operators'
                ),
                'issue_opened': True,
                'rich_text': False,
            },
            {
                'filediff_id': review_file.id,
                'first_line': 8,
                'num_lines': 1,
                'text': (
                    'Using C-style cast.  Use static_cast<int>(...) instead\n'
                    '\n'
                    'Error code: readability/casting'
                ),
                'issue_opened': True,
                'rich_text': False,
            },
        ])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                '--verbose=1',
                os.path.join(tmpdirs[-1], 'test.cc'),
            ],
            ignore_errors=True)

    @integration_test()
    @simulation_test(output='')
    def test_execute_with_success(self):
        """Testing CPPLintTool.execute with no warnings or errors"""
        review, review_file = self.run_tool_execute(
            filename='test.cc',
            file_contents=(
                b'/* Copyright (C) 2021 FooCorp, Inc. */\n'
                b'int main() {\n'
                b'    return 0;\n'
                b'}\n'
            ),
            tool_settings={
                'verbosity': 5,
            })

        self.assertEqual(review.comments, [])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                '--verbose=5',
                os.path.join(tmpdirs[-1], 'test.cc'),
            ],
            ignore_errors=True)

    def setup_simulation_test(self, output):
        """Set up the simulation test for pyflakes.

        This will spy on :py:func:`~reviewbot.utils.process.execute`, making
        it return the provided stdout and stderr results.

        Args:
            output (unicode):
                The outputted results from cpplint.
        """
        self.spy_on(execute, op=kgb.SpyOpReturn(output))
