"""Unit tests for reviewbot.tools.cppcheck."""

from __future__ import unicode_literals

import os

import kgb
import six

from reviewbot.tools.cppcheck import CPPCheckTool
from reviewbot.tools.testing import (BaseToolTestCase,
                                     ToolTestCaseMetaclass,
                                     integration_test,
                                     simulation_test)
from reviewbot.utils.filesystem import tmpdirs
from reviewbot.utils.process import execute


@six.add_metaclass(ToolTestCaseMetaclass)
class CPPCheckToolTests(BaseToolTestCase):
    """Unit tests for reviewbot.tools.cppcheck.CPPCheckTool."""

    tool_class = CPPCheckTool
    tool_exe_config_key = 'cppcheck'
    tool_exe_path = '/path/to/cppcheck'

    sample_cpp_code = (
        b'template <int i>\n'
        b'int test() {\n'
        b'    int buf[10];\n'
        b'    buf[100] = 0;\n'
        b'\n'
        b'    return test<i + 1>();\n'
        b'}\n'
        b'\n'
        b'int main() {\n'
        b'    return test<0>();\n'
        b'\n'
        b'    int i = 42;\n'
        b'}'
    )

    @integration_test()
    @simulation_test(output=(
        "4::8::error::arrayIndexOutOfBounds::Array 'buf[10]' accessed at "
        "index 100, which is out of bounds.\n"
    ))
    def test_execute(self):
        """Testing CPPCheckTool.execute"""
        review, review_file = self.run_tool_execute(
            filename='test.cc',
            file_contents=self.sample_cpp_code)

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 4,
                'num_lines': 1,
                'text': (
                    "Array 'buf[10]' accessed at index 100, which is out "
                    "of bounds.\n"
                    "\n"
                    "Column: 8\n"
                    "Severity: error\n"
                    "Error code: arrayIndexOutOfBounds"
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
                '--template={line}::{column}::{severity}::{id}::{message}',
                os.path.join(tmpdirs[-1], 'test.cc'),
            ],
            ignore_errors=True)

    @integration_test()
    @simulation_test(output=(
        "4::8::error::arrayIndexOutOfBounds::Array 'buf[10]' accessed at "
        "index 100, which is out of bounds.\n"

        "12::11::style::unreadVariable::Variable 'i' is assigned a value that "
        "is never used.\n"

        "4::14::style::unreadVariable::Variable 'buf[100]' is assigned a "
        "value that is never used.\n"
    ))
    def test_execute_with_style_checks_enabled(self):
        """Testing CPPCheckTool.execute with style_checks_enabled setting"""
        review, review_file = self.run_tool_execute(
            filename='test.cc',
            file_contents=self.sample_cpp_code,
            tool_settings={
                'style_checks_enabled': True,
            })

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 4,
                'num_lines': 1,
                'text': (
                    "Array 'buf[10]' accessed at index 100, which is out "
                    "of bounds.\n"
                    "\n"
                    "Column: 8\n"
                    "Severity: error\n"
                    "Error code: arrayIndexOutOfBounds"
                ),
                'issue_opened': True,
                'rich_text': False,
            },
            {
                'filediff_id': review_file.id,
                'first_line': 12,
                'num_lines': 1,
                'text': (
                    "Variable 'i' is assigned a value that is never used.\n"
                    "\n"
                    "Column: 11\n"
                    "Severity: style\n"
                    "Error code: unreadVariable"
                ),
                'issue_opened': True,
                'rich_text': False,
            },
            {
                'filediff_id': review_file.id,
                'first_line': 4,
                'num_lines': 1,
                'text': (
                    "Variable 'buf[100]' is assigned a value that is never "
                    "used.\n"
                    "\n"
                    "Column: 14\n"
                    "Severity: style\n"
                    "Error code: unreadVariable"
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
                '--template={line}::{column}::{severity}::{id}::{message}',
                '--enable=style',
                os.path.join(tmpdirs[-1], 'test.cc'),
            ],
            ignore_errors=True)

    @integration_test()
    @simulation_test(output=(
        "6::12::information::templateRecursion::TemplateSimplifier: max "
        "template recursion (100) reached for template 'test<101>'. You might "
        "want to limit Cppcheck recursion.\n"

        "4::8::error::arrayIndexOutOfBounds::Array 'buf[10]' accessed at "
        "index 100, which is out of bounds.\n"

        "12::11::style::unreadVariable::Variable 'i' is assigned a value that "
        "is never used.\n"

        "4::14::style::unreadVariable::Variable 'buf[100]' is assigned a "
        "value that is never used.\n"
    ))
    def test_execute_with_all_checks_enabled(self):
        """Testing CPPCheckTool.execute with all_checks_enabled setting"""
        review, review_file = self.run_tool_execute(
            filename='test.cc',
            file_contents=self.sample_cpp_code,
            tool_settings={
                'all_checks_enabled': True,
            })

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 6,
                'num_lines': 1,
                'text': (
                    "TemplateSimplifier: max template recursion (100) "
                    "reached for template 'test<101>'. You might want to "
                    "limit Cppcheck recursion.\n"
                    "\n"
                    "Column: 12\n"
                    "Severity: information\n"
                    "Error code: templateRecursion"
                ),
                'issue_opened': True,
                'rich_text': False,
            },
            {
                'filediff_id': review_file.id,
                'first_line': 4,
                'num_lines': 1,
                'text': (
                    "Array 'buf[10]' accessed at index 100, which is out "
                    "of bounds.\n"
                    "\n"
                    "Column: 8\n"
                    "Severity: error\n"
                    "Error code: arrayIndexOutOfBounds"
                ),
                'issue_opened': True,
                'rich_text': False,
            },
            {
                'filediff_id': review_file.id,
                'first_line': 12,
                'num_lines': 1,
                'text': (
                    "Variable 'i' is assigned a value that is never used.\n"
                    "\n"
                    "Column: 11\n"
                    "Severity: style\n"
                    "Error code: unreadVariable"
                ),
                'issue_opened': True,
                'rich_text': False,
            },
            {
                'filediff_id': review_file.id,
                'first_line': 4,
                'num_lines': 1,
                'text': (
                    "Variable 'buf[100]' is assigned a value that is never "
                    "used.\n"
                    "\n"
                    "Column: 14\n"
                    "Severity: style\n"
                    "Error code: unreadVariable"
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
                '--template={line}::{column}::{severity}::{id}::{message}',
                '--enable=all',
                os.path.join(tmpdirs[-1], 'test.cc'),
            ],
            ignore_errors=True)

    @integration_test()
    @simulation_test(output=(
        "6::22::error::syntaxError::syntax error: >()\n"
    ))
    def test_execute_with_force_language(self):
        """Testing CPPCheckTool.execute with force_language setting"""
        review, review_file = self.run_tool_execute(
            filename='test.cc',
            file_contents=self.sample_cpp_code,
            tool_settings={
                'force_language': 'c',
            })

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 6,
                'num_lines': 1,
                'text': (
                    "syntax error: >()\n"
                    "\n"
                    "Column: 22\n"
                    "Severity: error\n"
                    "Error code: syntaxError"
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
                '--template={line}::{column}::{severity}::{id}::{message}',
                '--language=c',
                os.path.join(tmpdirs[-1], 'test.cc'),
            ],
            ignore_errors=True)

    @integration_test()
    @simulation_test(output='')
    def test_execute_with_success(self):
        """Testing CPPCheckTool.execute with no warnings or errors"""
        review, review_file = self.run_tool_execute(
            filename='test.cc',
            file_contents=(
                b'int main() {\n'
                b'    return 0;\n'
                b'}\n'
            ))

        self.assertEqual(review.comments, [])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                '-q',
                '--template={line}::{column}::{severity}::{id}::{message}',
                os.path.join(tmpdirs[-1], 'test.cc'),
            ],
            ignore_errors=True)

    def setup_simulation_test(self, output):
        """Set up the simulation test for pyflakes.

        This will spy on :py:func:`~reviewbot.utils.process.execute`, making
        it return the provided stdout and stderr results.

        Args:
            output (unicode):
                The outputted results from cppcheck.
        """
        self.spy_on(execute, op=kgb.SpyOpReturn(output))
