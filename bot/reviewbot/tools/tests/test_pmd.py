"""Unit tests for reviewbot.tools.pmd."""

from __future__ import unicode_literals

import json
import os

import kgb
import six

from reviewbot.tools.pmd import PMDTool
from reviewbot.tools.testing import (BaseToolTestCase,
                                     ToolTestCaseMetaclass,
                                     integration_test,
                                     simulation_test)
from reviewbot.tools.base.mixins import JavaToolMixin
from reviewbot.utils.filesystem import tmpdirs, tmpfiles
from reviewbot.utils.process import execute, is_exe_in_path


@six.add_metaclass(ToolTestCaseMetaclass)
class PMDToolTests(BaseToolTestCase):
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
                        'endline': 7,
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

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 1,
                'num_lines': 7,
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
            [
                self.tool_exe_path,
                'pmd',
                '-no-cache',
                '-f', 'json',
                '-R', ('category/java/codestyle.xml/ShortClassName,'
                       'category/java/codestyle.xml/ControlStatementBraces'),
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
                        'endline': 7,
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

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 1,
                'num_lines': 7,
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

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                'pmd',
                '-no-cache',
                '-f', 'json',
                '-R', tmpfiles[-2],
                '-d', os.path.join(tmpdirs[-1], 'test.java'),
                '-r', tmpfiles[-1],
            ],
            ignore_errors=True)

    @integration_test()
    @simulation_test(stderr=(
        'SEVERE: No rules found. Maybe you misspelled a rule name? '
        '(<check ruleset configuration>)'
    ))
    def test_execute_with_ruleset_xml_bad(self):
        """Testing PMDTool.execute with ruleset configuration XML with
        validation problems
        """
        ruleset_xml = (
            '<?xml version="1.0"?>\n'
            '<bad-ruleset name="My Ruleset"\n'
            '         xmlns="http://pmd.sourceforge.net/ruleset/2.0.0"\n'
            '         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n'
            '         xsi:schemaLocation="'
            'http://pmd.sourceforge.net/ruleset/2.0.0 '
            'http://pmd.sourceforge.net/ruleset_2_0_0.xsd">\n'
            ' <description>My ruleset</description>\n'
            '</bad-ruleset>'
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

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 1,
                'num_lines': 1,
                'text': (
                    'PMD was unable to process this file:\n'
                    '\n'
                    '```\n'
                    'SEVERE: No rules found. Maybe you misspelled a rule '
                    'name? (<check ruleset configuration>)\n'
                    '```'
                ),
                'issue_opened': True,
                'rich_text': False,
            },
        ])
        self.assertEqual(review.general_comments, [])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                'pmd',
                '-no-cache',
                '-f', 'json',
                '-R', tmpfiles[-2],
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
            [
                self.tool_exe_path,
                'pmd',
                '-no-cache',
                '-f', 'json',
                '-R', 'category/java/codestyle.xml/ShortClassName',
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
                'message': 'PMDException: Error while parsing test.java'
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

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 1,
                'num_lines': 1,
                'text': (
                    'PMD was unable to process this file:\n'
                    '\n'
                    '```\n'
                    'PMDException: Error while parsing test.java\n'
                    '```\n'
                    '\n'
                    'Check the file locally for more information.'
                ),
                'issue_opened': True,
                'rich_text': False,
            },
        ])
        self.assertEqual(review.general_comments, [])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                'pmd',
                '-no-cache',
                '-f', 'json',
                '-R', 'category/java/codestyle.xml/ShortClassName',
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
            [
                self.tool_exe_path,
                'pmd',
                '-no-cache',
                '-f', 'json',
                '-R', 'category/java/codestyle.xml/ShortClassName',
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
            [
                self.tool_exe_path,
                'pmd',
                '-no-cache',
                '-f', 'json',
                '-R', 'category/java/codestyle.xml/ShortClassName',
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

        self.assertSpyNotCalled(execute)

    def setup_simulation_test(self, output_payload=None, stderr=''):
        """Set up the simulation test for PMD.

        This will spy on :py:func:`~reviewbot.utils.process.execute`, making
        it return the provided payload.

        Args:
            output_payload (dict):
                The output payload to serialize to JSON. If not provided, a
                file will not be written.

            stderr (unicode, optional):
                The error output to simulate from PMD.
        """
        assert isinstance(stderr, six.text_type)

        @self.spy_for(execute)
        def _execute(cmdline, *args, **kwargs):
            if output_payload is not None:
                with open(tmpfiles[-1], 'w') as fp:
                    json.dump(output_payload, fp)

            return ('stdout junk', stderr)
