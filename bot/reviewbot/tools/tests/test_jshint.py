"""Unit tests for reviewbot.tools.jshint."""

from __future__ import unicode_literals

import json
import os

import kgb
import six

from reviewbot.tools.jshint import JSHintTool
from reviewbot.tools.testing import (BaseToolTestCase,
                                     ToolTestCaseMetaclass,
                                     integration_test,
                                     simulation_test)
from reviewbot.utils.filesystem import tmpdirs, tmpfiles
from reviewbot.utils.process import execute


@six.add_metaclass(ToolTestCaseMetaclass)
class JSHintToolTests(BaseToolTestCase):
    """Unit tests for reviewbot.tools.jshint.JSHintTool."""

    tool_class = JSHintTool
    tool_exe_config_key = 'jshint'
    tool_exe_path = '/path/to/jshint'

    @integration_test()
    @simulation_test(output_payload=[
        {
            'code': 'W033',
            'column': 6,
            'line': 1,
            'msg': 'Missing semicolon.',
        },
        {
            'code': 'W107',
            'column': 41,
            'line': 3,
            'msg': 'Script URL.',
        },
    ])
    def test_execute(self):
        """Testing JSHintTool.execute"""
        review, review_file = self.run_tool_execute(
            filename='test.js',
            file_contents=(
                b'var a\n'
                b'\n'
                b'el.setAttribute("link", "javascript:foo");\n'
            ),
            tool_settings={
                'config': '',
                'extract_js_from_html': False,
            })

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 1,
                'num_lines': 1,
                'text': (
                    'Missing semicolon.\n'
                    '\n'
                    'Column: 6\n'
                    'Error code: W033'
                ),
                'issue_opened': True,
                'rich_text': False,
            },
            {
                'filediff_id': review_file.id,
                'first_line': 3,
                'num_lines': 1,
                'text': (
                    'Script URL.\n'
                    '\n'
                    'Column: 41\n'
                    'Error code: W107'
                ),
                'issue_opened': True,
                'rich_text': False,
            },
        ])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                '--extract=False',
                '--reporter=%s' % JSHintTool.REPORTER_PATH,
                os.path.join(tmpdirs[-1], 'test.js'),
            ],
            ignore_errors=True)

    @integration_test()
    @simulation_test(output_payload=[
        {
            'code': 'W107',
            'column': 41,
            'line': 3,
            'msg': 'Script URL.',
        },
    ])
    def test_execute_with_config(self):
        """Testing JSHintTool.execute with config setting"""
        review, review_file = self.run_tool_execute(
            filename='test.js',
            file_contents=(
                b'var a\n'
                b'\n'
                b'el.setAttribute("link", "javascript:foo");\n'
            ),
            tool_settings={
                'config': '{"asi": true}',
                'extract_js_from_html': False,
            })

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 3,
                'num_lines': 1,
                'text': (
                    'Script URL.\n'
                    '\n'
                    'Column: 41\n'
                    'Error code: W107'
                ),
                'issue_opened': True,
                'rich_text': False,
            },
        ])

        config_path = tmpfiles[-1]
        self.assertTrue(os.path.exists(config_path))

        with open(config_path, 'r') as fp:
            self.assertEqual(fp.read(), '{"asi": true}')

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                '--extract=False',
                '--reporter=%s' % JSHintTool.REPORTER_PATH,
                '--config=%s' % config_path,
                os.path.join(tmpdirs[-1], 'test.js'),
            ],
            ignore_errors=True)

    def setup_simulation_test(self, output_payload):
        """Set up the simulation test for JSHint.

        This will spy on :py:func:`~reviewbot.utils.process.execute`, making
        it return the provided payload.

        Args:
            output_payload (dict):
                The outputted payload.
        """
        self.spy_on(execute, op=kgb.SpyOpReturn(json.dumps(output_payload)))
