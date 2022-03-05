"""Unit tests for reviewbot.tools.fbinfer."""

from __future__ import unicode_literals

import json
import os
import tempfile
from unittest import SkipTest

import six

from reviewbot.config import config
from reviewbot.tools.fbinfer import FBInferTool
from reviewbot.tools.testing import (BaseToolTestCase,
                                     ToolTestCaseMetaclass,
                                     integration_test,
                                     simulation_test)
from reviewbot.utils.process import execute, is_exe_in_path


@six.add_metaclass(ToolTestCaseMetaclass)
class FBInferToolTests(BaseToolTestCase):
    """Unit tests for reviewbot.tools.fbinfer.FBInferTool."""

    tool_class = FBInferTool
    tool_exe_config_key = 'infer'
    tool_exe_path = '/path/to/fbinfer'

    def setUp(self):
        super(FBInferToolTests, self).setUp()

        self.checkout_dir = tempfile.mkdtemp()

    # NOTE: Simulated report payloads only contain the keys necessary.
    @integration_test(exe_deps=['javac'])
    @simulation_test(full_report=[
        {
            'bug_type_hum': 'Null Dereference',
            'column': -1,
            'file': 'Hello.java',
            'line': 4,
            'qualifier': (
                'object `s` last assigned on line 3 could be null and is '
                'dereferenced at line 4.'
            ),
            'severity': 'ERROR',
        },
    ])
    def test_execute_with_single_file_builds(self):
        """Testing FBInferTool.execute with single-file builds"""
        review, review_file = self.run_tool_execute(
            checkout_dir=self.checkout_dir,
            filename='Hello.java',
            file_contents=(
                b'class Hello {\n'
                b'    int test() {\n'
                b'        String s = null;\n'
                b'        return s.length();\n'
                b'    }\n'
                b'}\n'
            ),
            tool_settings={
                'build_type': 'javac',
            })

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 4,
                'issue_opened': True,
                'num_lines': 1,
                'rich_text': True,
                'text': (
                    'object `s` last assigned on line 3 could be null and '
                    'is dereferenced at line 4.\n'
                    '\n'
                    'Severity: ERROR\n'
                    'Error code: Null Dereference'
                ),
            },
        ])
        self.assertEqual(review.general_comments, [])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                'run',
                '--no-progress-bar',
                '--',
                'javac',
                'Hello.java',
            ],
            ignore_errors=True,
            with_errors=True)

    @integration_test(exe_deps=['gcc', 'make'])
    @simulation_test(full_report=[
        {
            'bug_type_hum': 'Null Dereference',
            'column': 12,
            'file': 'test1.c',
            'line': 5,
            'qualifier': (
                'pointer `i` last assigned on line 4 could be null and is '
                'dereferenced at line 5, column 12.'
            ),
            'severity': 'ERROR',
        },
        {
            'bug_type_hum': 'Dead Store',
            'column': 5,
            'file': 'test1.c',
            'line': 9,
            'qualifier': 'The value written to &p (type int*) is never used.',
            'severity': 'ERROR',
        },
        {
            'bug_type_hum': 'Resource Leak',
            'column': 5,
            'file': 'test2.c',
            'line': 7,
            'qualifier': (
                'resource acquired by call to `open()` at line 7, column 5 '
                'is not released after line 7, column 5.'
            ),
            'severity': 'ERROR',
        },
    ])
    def test_execute_with_multi_file_builds(self):
        """Testing FBInferTool.execute with multi-file builds"""
        review, review_files = self.run_tool_execute(
            checkout_dir=self.checkout_dir,
            filename='Makefile',
            file_contents=(
                b'all: test1.o test2.o\n'
                b'\n'
                b'.c.o:\n'
                b'\tgcc -c $<\n'
            ),
            other_files={
                'test1.c': (
                    b'#include <stdlib.h>\n'
                    b'\n'
                    b'int null_deref() {\n'
                    b'    int* i = NULL;\n'
                    b'    return *i;\n'
                    b'}\n'
                    b'\n'
                    b'void mem_leak() {\n'
                    b'    int* p = (int*)malloc(sizeof(int));\n'
                    b'}\n'
                ),
                'test2.c': (
                    b'#include <fcntl.h>\n'
                    b'#include <stdio.h>\n'
                    b'#include <stdlib.h>\n'
                    b'#include <unistd.h>\n'
                    b'\n'
                    b'void fp_leak() {\n'
                    b'    open("foo.txt", O_WRONLY);\n'
                    b'}\n'
                ),
            },
            tool_settings={
                'build_type': 'make',
            })

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_files['test1.c'].id,
                'first_line': 5,
                'issue_opened': True,
                'num_lines': 1,
                'rich_text': True,
                'text': (
                    'pointer `i` last assigned on line 4 could be null and '
                    'is dereferenced at line 5, column 12.\n'
                    '\n'
                    'Column: 12\n'
                    'Severity: ERROR\n'
                    'Error code: Null Dereference'
                ),
            },
            {
                'filediff_id': review_files['test1.c'].id,
                'first_line': 9,
                'issue_opened': True,
                'num_lines': 1,
                'rich_text': True,
                'text': (
                    'The value written to &p (type int*) is never used.\n'
                    '\n'
                    'Column: 5\n'
                    'Severity: ERROR\n'
                    'Error code: Dead Store'
                ),
            },
            {
                'filediff_id': review_files['test2.c'].id,
                'first_line': 7,
                'issue_opened': True,
                'num_lines': 1,
                'rich_text': True,
                'text': (
                    'resource acquired by call to `open()` at line 7, column '
                    '5 is not released after line 7, column 5.\n'
                    '\n'
                    'Column: 5\n'
                    'Severity: ERROR\n'
                    'Error code: Resource Leak'
                ),
            },
        ])
        self.assertEqual(review.general_comments, [])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                'run',
                '--no-progress-bar',
                '--',
                'make',
            ],
            ignore_errors=True,
            with_errors=True)

    @integration_test(exe_deps=['cmake'])
    @simulation_test(full_report=[
        {
            'bug_type_hum': 'Null Dereference',
            'column': 12,
            'file': 'test.c',
            'line': 5,
            'qualifier': (
                'pointer `i` last assigned on line 4 could be null and is '
                'dereferenced at line 5, column 12.'
            ),
            'severity': 'ERROR',
        },
        {
            'bug_type_hum': 'Dead Store',
            'column': 5,
            'file': 'test.c',
            'line': 9,
            'qualifier': 'The value written to &p (type int*) is never used.',
            'severity': 'ERROR',
        },
    ])
    def test_execute_with_cmake(self):
        """Testing FBInferTool.execute with cmake"""
        review, review_files = self.run_tool_execute(
            checkout_dir=self.checkout_dir,
            filename='CMakeLists.txt',
            file_contents=(
                b'cmake_minimum_required (VERSION 2.8.11)\n'
                b'project (TEST)\n'
                b'add_library (Test test.c)\n'
            ),
            other_files={
                'test.c': (
                    b'#include <stdlib.h>\n'
                    b'\n'
                    b'int null_deref() {\n'
                    b'    int* i = NULL;\n'
                    b'    return *i;\n'
                    b'}\n'
                    b'\n'
                    b'void mem_leak() {\n'
                    b'    int* p = (int*)malloc(sizeof(int));\n'
                    b'}\n'
                ),
            },
            tool_settings={
                'build_type': 'cmake',
            })

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_files['test.c'].id,
                'first_line': 5,
                'issue_opened': True,
                'num_lines': 1,
                'rich_text': True,
                'text': (
                    'pointer `i` last assigned on line 4 could be null and '
                    'is dereferenced at line 5, column 12.\n'
                    '\n'
                    'Column: 12\n'
                    'Severity: ERROR\n'
                    'Error code: Null Dereference'
                ),
            },
            {
                'filediff_id': review_files['test.c'].id,
                'first_line': 9,
                'issue_opened': True,
                'num_lines': 1,
                'rich_text': True,
                'text': (
                    'The value written to &p (type int*) is never used.\n'
                    '\n'
                    'Column: 5\n'
                    'Severity: ERROR\n'
                    'Error code: Dead Store'
                ),
            },
        ])
        self.assertEqual(review.general_comments, [])

        self.assertSpyCallCount(execute, 2)
        self.assertSpyCalledWith(
            execute.calls[0],
            [
                self.tool_exe_path,
                'compile',
                '--',
                'cmake',
                '.',
            ],
            with_errors=True)

        self.assertSpyCalledWith(
            execute.calls[1],
            [
                self.tool_exe_path,
                'run',
                '--no-progress-bar',
                '--',
                'make',
            ],
            ignore_errors=True,
            with_errors=True)

    @integration_test(exe_deps=['cmake'])
    @simulation_test(compile_error=True)
    def test_execute_with_cmake_and_compile_error(self):
        """Testing FBInferTool.execute with cmake and infer compile error"""
        review, review_files = self.run_tool_execute(
            checkout_dir=self.checkout_dir,
            filename='CMakeLists.txt',
            file_contents=(
                b'cmake_minimum_required (VERSION 2.8.11)\n'
                b'zproject (TEST)\n'
                b'badd_library (Test test.c)\n'
            ),
            other_files={
                'test.c': (
                    b'#include <stdlib.h>\n'
                    b'\n'
                    b'int null_deref() {\n'
                    b'    int* i = NULL;\n'
                    b'    return *i;\n'
                    b'}\n'
                    b'\n'
                    b'void mem_leak() {\n'
                    b'    int* p = (int*)malloc(sizeof(int));\n'
                    b'}\n'
                ),
            },
            tool_settings={
                'build_type': 'cmake',
            })

        self.assertEqual(review.general_comments, [{
            'issue_opened': True,
            'rich_text': True,
            'text': 'FBInfer was unable to build this project using CMake.'
        }])
        self.assertEqual(review.comments, [])

        self.assertSpyCallCount(execute, 1)
        self.assertSpyCalledWith(
            execute.calls[0],
            [
                self.tool_exe_path,
                'compile',
                '--',
                'cmake',
                '.',
            ],
            with_errors=True)

    def setup_integration_test(self, exe_deps, **kwargs):
        """Set up an integration test.

        Args:
            exe_deps (list of unicode):
                Dependencies required by this test.

            **kwargs (dict):
                Keyword arguments passed to
                :py:func:`~reviewbot.tools.testing.testcases.integration_test`.
        """
        exe_paths = config['exe_paths']

        for exe_dep in exe_deps:
            if not is_exe_in_path(exe_dep, cache=exe_paths):
                raise SkipTest('%s was not found in the path' % exe_dep)

    def setup_simulation_test(self, compile_error=False, file_error=False,
                              full_report=None, output=None):
        """Set up the simulation test for cargotool.

        This will spy on :py:func:`~reviewbot.utils.process.execute`, making
        it return the provided data.

        Args:
            compile_error (bool, optional):
                Whether to return an error when compiling.

            file_error (bool, optional):
                Whether to return an error when executing infer on a file.

            full_report (list, optional):
                A full report file contents to write.

            output (unicode, optional):
                Output to return when executing a command.
        """
        if full_report is not None:
            report_dir = os.path.join(self.checkout_dir, 'infer-out')

            os.mkdir(report_dir, 0o755)

            with open(os.path.join(report_dir, 'report.json'), 'w') as fp:
                json.dump(full_report, fp)

        @self.spy_for(execute)
        def _execute(command, *args, **kwargs):
            if compile_error and command[1] == 'compile':
                raise Exception('Failed to execute command: %s' % command)
            elif file_error and command[1] != 'compile':
                raise Exception('FBInfer was unable to build `%s`.'
                                % command[-1])

            return output
