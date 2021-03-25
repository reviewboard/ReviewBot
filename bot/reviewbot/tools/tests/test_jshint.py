"""Unit tests for reviewbot.tools.jshint."""

from __future__ import unicode_literals

import json
import os
from unittest import SkipTest

import kgb

import reviewbot
from reviewbot.testing import TestCase
from reviewbot.tools.jshint import JSHintTool
from reviewbot.utils.filesystem import tmpfiles
from reviewbot.utils.process import execute


class BaseJSHintToolTests(kgb.SpyAgency, TestCase):
    """Base class for reviewbot.tools.jshint.JSHintTool tests."""

    jshint_path = None

    def check_execute(self):
        """Common tests for execute."""
        review, review_file = self._run_execute(
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
                self.jshint_path,
                '--extract=False',
                '--reporter=%s' % JSHintTool.REPORTER_PATH,
                tmpfiles[-1],
            ],
            ignore_errors=True)

    def check_execute_with_config(self):
        """Common tests for execute with a config setting."""
        review, review_file = self._run_execute(
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

        config_path = tmpfiles[-2]
        self.assertTrue(os.path.exists(config_path))

        with open(config_path, 'r') as fp:
            self.assertEqual(fp.read(), '{"asi": true}')

        self.assertSpyCalledWith(
            execute,
            [
                self.jshint_path,
                '--extract=False',
                '--reporter=%s' % JSHintTool.REPORTER_PATH,
                '--config=%s' % config_path,
                tmpfiles[-1],
            ],
            ignore_errors=True)

    def _run_execute(self, file_contents, tool_settings={}):
        """Set up and run a execute test.

        This will create the review objects, configure the path to
        jshint, and run the test.

        Args:
            settings (dict):
                The settings to pass to
                :py:meth:`~reviewbot.tools.jshint.JSHintTool.execute`.

        Returns:
            tuple:
            A tuple containing the review and the file.
        """
        review = self.create_review()
        review_file = self.create_review_file(
            review,
            source_file='test.js',
            dest_file='test.js',
            diff_data=self.create_diff_data(chunks=[{
                'change': 'insert',
                'lines': file_contents.splitlines(),
                'new_linenum': 1,
            }]),
            patched_content=file_contents)

        new_config = {
            'exe_paths': {
                'jshint': self.jshint_path,
            },
        }

        with self.override_config(new_config):
            tool = JSHintTool(settings=tool_settings)
            tool.execute(review)

        return review, review_file


class JSHintToolTests(BaseJSHintToolTests):
    """Unit tests for reviewbot.tools.jshint.JSHintTool."""

    def test_execute(self):
        """Testing JSHintTool.execute"""
        self.spy_on(execute, op=kgb.SpyOpReturn(json.dumps([
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
        ])))

        self.check_execute()

    def test_execute_with_config(self):
        """Testing JSHintTool.execute with config setting"""
        self.spy_on(execute, op=kgb.SpyOpReturn(json.dumps([
            {
                'code': 'W107',
                'column': 41,
                'line': 3,
                'msg': 'Script URL.',
            },
        ])))

        self.check_execute_with_config()


class JSHintToolIntegrationTests(BaseJSHintToolTests):
    """Integration tests for reviewbot.tools.jshint.JSHintTool."""

    preserve_path_env = True

    def setUp(self):
        super(JSHintToolIntegrationTests, self).setUp()

        self.jshint_path = os.path.abspath(
            os.path.join(reviewbot.__file__, '..', '..', 'node_modules',
                         '.bin', 'jshint'))

        if not os.path.exists(self.jshint_path):
            raise SkipTest('jshint dependencies not available')

        self.spy_on(execute)

    def test_execute(self):
        """Testing JSHintTool.execute with jshint binary"""
        self.check_execute()

    def test_execute_with_config(self):
        """Testing JSHintTool.execute with jshint binary and config setting"""
        self.check_execute_with_config()
