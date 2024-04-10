"""Unit tests for reviewbot.tools.pmd."""

from __future__ import annotations

import json
import os
from typing import Any, Optional

import kgb

from reviewbot.tools.pmd import PMDTool
from reviewbot.tools.testing import (BaseToolTestCase,
                                     ToolTestCaseMetaclass,
                                     integration_test,
                                     simulation_test)
from reviewbot.tools.base.mixins import JavaToolMixin
from reviewbot.utils.filesystem import tmpdirs, tmpfiles
from reviewbot.utils.process import execute, is_exe_in_path


class PMDToolTests(BaseToolTestCase, metaclass=ToolTestCaseMetaclass):
    """Unit tests for reviewbot.tools.pmd.PMDTool."""

    tool_class = PMDTool
    tool_exe_config_key = 'pmd'
    tool_exe_path = '/path/to/pmd'
    tool_extra_exe_paths = {
        'java': '/path/to/java',
    }

    def test_check_dependencies_with_no_config(self):
        """Testing PMDTool.check_dependencies with no configured pmd_path"""
        with self.override_config({}):
            tool = PMDTool()
            self.assertFalse(tool.check_dependencies())

    def test_check_dependencies_with_pmd_not_found(self):
        """Testing PMDTool.check_dependencies with configured pmd_path not
        found on filesystem
        """
        self.spy_on(is_exe_in_path, op=kgb.SpyOpMatchInOrder([
            {
                'args': ('/path/to/java',),
                'op': kgb.SpyOpReturn(True),
            },
            {
                'args': ('/path/to/pmd',),
                'op': kgb.SpyOpReturn(False),
            },
        ]))

        new_config = {
            'exe_paths': {
                'java': '/path/to/java',
                'pmd': '/path/to/pmd',
            }
        }

        JavaToolMixin.set_has_java_runtime(True)

        try:
            with self.override_config(new_config):
                tool = PMDTool()
                self.assertFalse(tool.check_dependencies())
        finally:
            JavaToolMixin.clear_has_java_runtime()

        self.assertSpyCalledWith(is_exe_in_path, '/path/to/java')
        self.assertSpyCalledWith(is_exe_in_path, '/path/to/pmd')

    def test_check_dependencies_with_pmd_found(self):
        """Testing PMDTool.check_dependencies with configured pmd_path
        found on filesystem
        """
        self.spy_on(is_exe_in_path, op=kgb.SpyOpReturn(True))

        new_config = {
            'exe_paths': {
                'java': '/path/to/java',
                'pmd': '/path/to/pmd',
            }
        }

        JavaToolMixin.set_has_java_runtime(True)

        try:
            with self.override_config(new_config):
                tool = PMDTool()
                self.assertTrue(tool.check_dependencies())
                self.assertSpyCalledWith(is_exe_in_path, '/path/to/pmd')
        finally:
            JavaToolMixin.clear_has_java_runtime()

    @integration_test()
    @simulation_test(output_payload={
        'formatVersion': 0,
        'pmdVersion': '6.32.0',
        'timestamp': '2021-03-26T03:18:12.692-07:00',
        'files': [
            {
                'filename': '/path/to/test.java',
                'violations': [
                    {
                        'begincolumn': 8,
                        'beginline': 1,
                        'description': 'Avoid short class names like Cls',
                        'endcolumn': 1,
                        'endline': 1,
                        'externalInfoUrl': (
                            'https://pmd.github.io/pmd-6.32.0/'
                            'pmd_rules_java_codestyle.html'
                            '#shortclassname'
                        ),
                        'priority': 4,
                        'rule': 'ShortClassName',
                        'ruleset': 'Code Style',
                    },
                    {
                        'begincolumn': 13,
                        'beginline': 4,
                        'description': 'This statement should have braces',
                        'endcolumn': 21,
                        'endline': 4,
                        'externalInfoUrl': (
                            'https://pmd.github.io/pmd-6.32.0/'
                            'pmd_rules_java_codestyle.html'
                            '#controlstatementbraces'
                        ),
                        'priority': 4,
                        'rule': 'ShortClassName',
                        'ruleset': 'Code Style',
                    },
                ],
            },
        ],
    })
    def test_execute_with_ruleset_names(self):
        """Testing PMDTool.execute with ruleset names"""
        review, review_file = self.run_tool_execute(
            filename='test.java',
            file_contents=(
                b'public class Cls {\n'
                b'    public int a(int b) {\n'
                b'        if (b == true)\n'
                b'            return 1;\n'
                b'        return 0;\n'
                b'    }\n'
                b'}\n'
            ),
            tool_settings={
                'file_ext': '',
                'rulesets': (
                    'category/java/codestyle.xml/ShortClassName,'
                    'category/java/codestyle.xml/ControlStatementBraces'
                ),
            })

        # PMD 7 has a much better span for this particular rule.
        if self.tool.pmd_version == 7:
            class_names_num_lines = 1
        else:
            class_names_num_lines = 7

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 1,
                'num_lines': class_names_num_lines,
                'text': (
                    'Avoid short class names like Cls\n'
                    '\n'
                    'Column: 8'
                ),
                'issue_opened': True,
                'rich_text': False,
            },
            {
                'filediff_id': review_file.id,
                'first_line': 4,
                'num_lines': 1,
                'text': (
                    'This statement should have braces\n'
                    '\n'
                    'Column: 13'
                ),
                'issue_opened': True,
                'rich_text': False,
            },
        ])
        self.assertEqual(review.general_comments, [])

        self.assertSpyCalledWith(
            execute,
            self.tool._base_command + [
                '-d', os.path.join(tmpdirs[-1], 'test.java'),
                '-r', tmpfiles[-1],
            ],
            ignore_errors=True)

    @integration_test()
    @simulation_test(output_payload={
        'formatVersion': 0,
        'pmdVersion': '6.32.0',
        'timestamp': '2021-03-26T03:18:12.692-07:00',
        'files': [
            {
                'filename': '/path/to/test.java',
                'violations': [
                    {
                        'begincolumn': 8,
                        'beginline': 1,
                        'description': 'Avoid short class names like Cls',
                        'endcolumn': 1,
                        'endline': 1,
                        'externalInfoUrl': (
                            'https://pmd.github.io/pmd-6.32.0/'
                            'pmd_rules_java_codestyle.html'
                            '#shortclassname'
                        ),
                        'priority': 4,
                        'rule': 'ShortClassName',
                        'ruleset': 'Code Style',
                    },
                ],
            },
        ],
    })
    def test_execute_with_ruleset_xml(self):
        """Testing PMDTool.execute with ruleset configuration XML"""
        ruleset_xml = (
            '<?xml version="1.0"?>\n'
            '<ruleset name="My Ruleset"\n'
            '         xmlns="http://pmd.sourceforge.net/ruleset/2.0.0"\n'
            '         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n'
            '         xsi:schemaLocation="'
            'http://pmd.sourceforge.net/ruleset/2.0.0 '
            'http://pmd.sourceforge.net/ruleset_2_0_0.xsd">\n'
            ' <description>This is a test ruleset</description>\n'
            ' <rule ref="category/java/codestyle.xml/ShortClassName"/>\n'
            '</ruleset>'
        )

        review, review_file = self.run_tool_execute(
            filename='test.java',
            file_contents=(
                b'public class Cls {\n'
                b'    public int a(int b) {\n'
                b'        if (b == true)\n'
                b'            return 1;\n'
                b'        return 0;\n'
                b'    }\n'
                b'}\n'
            ),
            tool_settings={
                'file_ext': '',
                'rulesets': ruleset_xml,
            })

        # PMD 7 has a much better span for this particular rule.
        if self.tool.pmd_version == 7:
            class_names_num_lines = 1
        else:
            class_names_num_lines = 7

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 1,
                'num_lines': class_names_num_lines,
                'text': (
                    'Avoid short class names like Cls\n'
                    '\n'
                    'Column: 8'
                ),
                'issue_opened': True,
                'rich_text': False,
            },
        ])
        self.assertEqual(review.general_comments, [])

        # We can't use build_base_command again here to check the full
        # assertSpyCalledWith because it will generate a new tempfile for the
        # rulesets. Just compare the last elements in the command-line.
        self.assertEqual(
            execute.last_call.args[0][-4:],
            [
                '-d', os.path.join(tmpdirs[-1], 'test.java'),
                '-r', tmpfiles[-1],
            ])

    @integration_test()
    @simulation_test(output_payload={
        'formatVersion': 0,
        'pmdVersion': '6.32.0',
        'timestamp': '2021-03-26T03:18:12.692-07:00',
        'files': [
            {
                'filename': '/path/to/test.java',
                'violations': [],
            },
        ],
    })
    def test_execute_with_no_errors(self):
        """Testing PMDTool.execute with no errors"""
        review, review_file = self.run_tool_execute(
            filename='test.java',
            file_contents=(
                b'public class MyClass {\n'
                b'    public void foo() {\n'
                b'    }\n'
                b'}\n'
            ),
            tool_settings={
                'file_ext': '',
                'rulesets': 'category/java/codestyle.xml/ShortClassName',
            })

        self.assertEqual(review.comments, [])
        self.assertEqual(review.general_comments, [])

        self.assertSpyCalledWith(
            execute,
            self.tool._base_command + [
                '-d', os.path.join(tmpdirs[-1], 'test.java'),
                '-r', tmpfiles[-1],
            ],
            ignore_errors=True)

    @integration_test()
    @simulation_test(output_payload={
        'formatVersion': 0,
        'pmdVersion': '6.32.0',
        'timestamp': '2021-03-26T03:18:12.692-07:00',
        'files': [],
        'processingErrors': [
            {
                'filename': '/path/to/test.java',
                'message': (
                    'ParseException: Parse exception in file \'test.java\' '
                    'at line 1, column 8: Encountered <IDENTIFIER: "Bagel">.\n'
                    'Was expecting one of:\n'
                    '    "class" ...\n'
                    '    "interface" ...\n'
                    '    "@" ...\n'
                ),
            },
        ],
    })
    def test_execute_with_syntax_errors(self):
        """Testing PMDTool.execute with syntax errors"""
        review, review_file = self.run_tool_execute(
            filename='test.java',
            file_contents=(
                b'public Bagel!'
            ),
            tool_settings={
                'file_ext': '',
                'rulesets': 'category/java/codestyle.xml/ShortClassName',
            })

        if self.tool_exe_path == '/path/to/pmd':
            # Running in simulation mode.
            filename = 'test.java'
        else:
            # Running in integration mode.
            filename = f'{tmpdirs[-1]}/test.java'

        if self.tool.pmd_version == 7:
            error_text = (
                f'PMD was unable to process this file:\n'
                f'\n'
                f'```\n'
                f'ParseException: Parse exception in file \'{filename}\' '
                f'at line 1, column 8: Encountered <IDENTIFIER: "Bagel">.\n'
                f'Was expecting one of:\n'
                f'    "class" ...\n'
                f'    "interface" ...\n'
                f'    "@" ...\n'
                f'```\n'
                f'\n'
                f'Check the file locally for more information.'
            )
        else:
            error_text = (
                f'PMD was unable to process this file:\n'
                f'\n'
                f'```\n'
                f'PMDException: Error while parsing {filename}\n'
                f'```\n'
                f'\n'
                f'Check the file locally for more information.'
            )

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 1,
                'num_lines': 1,
                'text': error_text,
                'issue_opened': True,
                'rich_text': False,
            },
        ])
        self.assertEqual(review.general_comments, [])

        self.assertSpyCalledWith(
            execute,
            self.tool._base_command + [
                '-d', os.path.join(tmpdirs[-1], 'test.java'),
                '-r', tmpfiles[-1],
            ],
            ignore_errors=True)

    @integration_test()
    @simulation_test(output_payload={
        'formatVersion': 0,
        'pmdVersion': '6.32.0',
        'timestamp': '2021-03-26T03:18:12.692-07:00',
        'files': [
            {
                'filename': '/path/to/test.java',
                'violations': [],
            },
        ],
    })
    def test_execute_with_file_ext_match(self):
        """Testing PMDTool.execute when file_ext matches"""
        review, review_file = self.run_tool_execute(
            filename='test.java',
            file_contents=(
                b'public class MyClass {\n'
                b'    public void foo() {\n'
                b'    }\n'
                b'}\n'
            ),
            tool_settings={
                'file_ext': 'c,py,java',
                'rulesets': 'category/java/codestyle.xml/ShortClassName',
            })

        self.assertEqual(review.comments, [])
        self.assertEqual(review.general_comments, [])

        self.assertSpyCalledWith(
            execute,
            self.tool._base_command + [
                '-d', os.path.join(tmpdirs[-1], 'test.java'),
                '-r', tmpfiles[-1],
            ],
            ignore_errors=True)

    @integration_test()
    @simulation_test(output_payload={
        'formatVersion': 0,
        'pmdVersion': '6.32.0',
        'timestamp': '2021-03-26T03:18:12.692-07:00',
        'files': [
            {
                'filename': '/path/to/test.java',
                'violations': [],
            },
        ],
    })
    def test_execute_with_file_ext_match_variants(self):
        """Testing PMDTool.execute when file_ext matches with variations
        in file extension configuration
        """
        review, review_file = self.run_tool_execute(
            filename='test.java',
            file_contents=(
                b'public class MyClass {\n'
                b'    public void foo() {\n'
                b'    }\n'
                b'}\n'
            ),
            tool_settings={
                'file_ext': 'c,, .py,  .java  ',
                'rulesets': 'category/java/codestyle.xml/ShortClassName',
            })

        self.assertEqual(review.comments, [])
        self.assertEqual(review.general_comments, [])

        self.assertSpyCalledWith(
            execute,
            self.tool._base_command + [
                '-d', os.path.join(tmpdirs[-1], 'test.java'),
                '-r', tmpfiles[-1],
            ],
            ignore_errors=True)

    @integration_test()
    @simulation_test()
    def test_execute_without_file_ext_match(self):
        """Testing PMDTool.execute when file_ext doesn't match"""
        review, review_file = self.run_tool_execute(
            filename='test.java',
            file_contents=(
                b'public class MyClass {\n'
                b'    public void foo() {\n'
                b'    }\n'
                b'}\n'
            ),
            tool_settings={
                'file_ext': 'txt,pyxyz',
                'rulesets': 'category/java/codestyle.xml/ShortClassName',
            })

        self.assertEqual(review.comments, [])
        self.assertEqual(review.general_comments, [])

        n_calls = len(execute.calls)

        # Make sure that the only calls we got were to check the PMD version.
        self.assertIn(n_calls, (1, 2))

        if n_calls > 1:
            self.assertSpyCalledWith(
                execute,
                [self.tool_exe_path, '--version'])

        if n_calls > 2:
            self.assertSpyCalledWith(
                execute,
                [self.tool_exe_path, 'pmd', '--version'])

    def setup_simulation_test(
        self,
        output_payload: Optional[dict[str, Any]] = None,
        stderr: str = '',
    ) -> None:
        """Set up the simulation test for PMD.

        This will spy on :py:func:`~reviewbot.utils.process.execute`, making
        it return the provided payload.

        Args:
            output_payload (dict):
                The output payload to serialize to JSON. If not provided, a
                file will not be written.

            stderr (str, optional):
                The error output to simulate from PMD.
        """
        assert isinstance(stderr, str)

        def _execute(cmdline, *args, **kwargs):
            if output_payload is not None:
                with open(tmpfiles[-1], 'w') as fp:
                    json.dump(output_payload, fp)

            return ('stdout junk', stderr)

        self.spy_on(execute, op=kgb.SpyOpMatchInOrder([
            {
                'args': (
                    [self.tool_exe_path, '--version'],
                ),
                'op': kgb.SpyOpReturn('PMD 7.0.0'),
            },
            {
                'call_fake': _execute,
            },
        ]))
