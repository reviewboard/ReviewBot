"""Unit tests for reviewbot.tools.pycodestyle."""

from __future__ import unicode_literals

from unittest import SkipTest

import kgb

from reviewbot.config import config
from reviewbot.testing import TestCase
from reviewbot.tools.pycodestyle import PycodestyleTool
from reviewbot.utils.filesystem import tmpfiles
from reviewbot.utils.process import execute


class BasePycodestyleToolTests(kgb.SpyAgency, TestCase):
    """Base class for PyCodestyleTool unit tests."""

    pycodestyle_path = None

    def check_execute(self):
        """Common tests for execute."""
        review, review_file = self._run_execute(
            file_contents=(
                b'try:\n'
                b'    func()\n'
                b'except:\n'
                b'    pass\n'
                b'\n'
                b'if d.has_key():\n'
                b'    pass\n'
            ),
            tool_settings={
                'max_line_length': 79,
            })

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 3,
                'num_lines': 1,
                'text': (
                    "do not use bare 'except'\n"
                    "\n"
                    "Column: 1\n"
                    "Error code: E722"
                ),
                'issue_opened': True,
                'rich_text': False,
            },
            {
                'filediff_id': review_file.id,
                'first_line': 6,
                'num_lines': 1,
                'text': (
                    ".has_key() is deprecated, use 'in'\n"
                    "\n"
                    "Column: 5\n"
                    "Error code: W601"
                ),
                'issue_opened': True,
                'rich_text': False,
            },
        ])

        self.assertSpyCalledWith(
            execute,
            [
                self.pycodestyle_path,
                '--max-line-length=79',
                '--format=%(code)s:%(row)d:%(col)d:%(text)s',
                tmpfiles[-1],
            ],
            ignore_errors=True)

    def check_execute_with_ignore(self):
        """Common tests for execute with ignore."""
        review, review_file = self._run_execute(
            file_contents=(
                b'try:\n'
                b'    func()\n'
                b'except:\n'
                b'    pass\n'
                b'\n'
                b'if d.has_key():\n'
                b'    pass\n'
            ),
            tool_settings={
                'max_line_length': 79,
                'ignore': 'W123,E722',
            })

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 6,
                'num_lines': 1,
                'text': (
                    ".has_key() is deprecated, use 'in'\n"
                    "\n"
                    "Column: 5\n"
                    "Error code: W601"
                ),
                'issue_opened': True,
                'rich_text': False,
            },
        ])

        self.assertSpyCalledWith(
            execute,
            [
                self.pycodestyle_path,
                '--max-line-length=79',
                '--format=%(code)s:%(row)d:%(col)d:%(text)s',
                '--ignore=W123,E722',
                tmpfiles[-1],
            ],
            ignore_errors=True)

    def _run_execute(self, file_contents, tool_settings={}):
        """Set up and run a execute test.

        This will create the review objects, configure the path to
        pycodestyle, and run the test.

        Args:
            settings (dict):
                The settings to pass to
                :py:meth:`~reviewbot.tools.pycodestyle.PycodestyleTool
                .execute`.

        Returns:
            tuple:
            A tuple containing the review and the file.
        """
        review = self.create_review()
        review_file = self.create_review_file(
            review,
            source_file='test.py',
            dest_file='test.py',
            diff_data=self.create_diff_data(chunks=[{
                'change': 'insert',
                'lines': file_contents.splitlines(),
                'new_linenum': 1,
            }]),
            patched_content=file_contents)

        new_config = {
            'exe_paths': {
                'pycodestyle': self.pycodestyle_path,
            },
        }

        with self.override_config(new_config):
            tool = PycodestyleTool(settings=tool_settings)
            tool.execute(review)

        return review, review_file


class PycodestyleToolTests(BasePycodestyleToolTests):
    """Unit tests for reviewbot.tools.pycodestyle.PycodestyleTool."""

    pycodestyle_path = '/path/to/pycodestyle'

    def test_execute(self):
        """Testing PycodestyleTool.execute"""
        self.spy_on(execute, op=kgb.SpyOpReturn([
            "E722:3:1:do not use bare 'except'",
            "W601:6:5:.has_key() is deprecated, use 'in'",
        ]))

        self.check_execute()

    def test_execute_with_ignore(self):
        """Testing PycodestyleTool.execute with ignore"""
        self.spy_on(execute, op=kgb.SpyOpReturn([
            "W601:6:5:.has_key() is deprecated, use 'in'",
        ]))

        self.check_execute_with_ignore()


class PycodestyleToolIntegrationTests(BasePycodestyleToolTests):
    """Integration tests for reviewbot.tools.pycodestyle.PycodestyleTool."""

    preserve_path_env = True

    def setUp(self):
        super(PycodestyleToolIntegrationTests, self).setUp()

        if not PycodestyleTool().check_dependencies():
            raise SkipTest('pycodestyle dependencies not available')

        self.pycodestyle_path = config['exe_paths']['pycodestyle']

        self.spy_on(execute)

    def test_execute(self):
        """Testing PycodestyleTool.execute with pycodestyle binary"""
        self.check_execute()

    def test_execute_with_ignore(self):
        """Testing PycodestyleTool.execute with pycodestyle binary and ignore
        """
        self.check_execute_with_ignore()
