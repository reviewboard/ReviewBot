"""Unit tests for reviewbot.tools.BaseTool."""

from __future__ import unicode_literals

import os
import shutil
import tempfile
from contextlib import contextmanager

import kgb

from reviewbot.testing import TestCase
from reviewbot.tools import BaseTool


class DummyTool(BaseTool):
    exe_dependencies = ['foo', 'bar']


class BaseToolTests(kgb.SpyAgency, TestCase):
    """Unit tests for reviewbot.tools.BaseTool."""

    def test_check_dependencies_with_all_found_in_path(self):
        """Testing BaseTool.check_dependencies with executable dependencies
        found in path
        """
        tool = DummyTool()

        with self._setup_deps(['foo', 'bar']):
            self.assertTrue(tool.check_dependencies())

            # Make sure a second call produces the same results (since
            # a cache will be updated).
            self.assertTrue(tool.check_dependencies())

    def test_check_dependencies_with_config_and_files_found(self):
        """Testing BaseTool.check_dependencies with exe_paths configuration
        and files found
        """
        tool = DummyTool()

        with self._setup_deps(['foo', 'bar'], set_path=False) as tempdir:
            new_config = {
                'exe_paths': {
                    'foo': os.path.join(tempdir, 'foo'),
                    'bar': os.path.join(tempdir, 'bar'),
                },
            }

            with self.override_config(new_config):
                self.assertTrue(tool.check_dependencies())

                # Make sure a second call produces the same results (since
                # a cache will be updated).
                self.assertTrue(tool.check_dependencies())

    def test_check_dependencies_with_config_and_files_not_found(self):
        """Testing BaseTool.check_dependencies with exe_paths configuration
        and configured files not found
        """
        tool = DummyTool()

        with self._setup_deps(set_path=False) as tempdir:
            new_config = {
                'exe_paths': {
                    'foo': os.path.join(tempdir, 'foo'),
                    'bar': os.path.join(tempdir, 'bar'),
                },
            }

            with self.override_config(new_config):
                self.assertFalse(tool.check_dependencies())

                # Make sure a second call produces the same results (since
                # a cache will be updated).
                self.assertFalse(tool.check_dependencies())

    def test_check_dependencies_with_missing_deps(self):
        """Testing BaseTool.check_dependencies with executable dependency
        missing
        """
        tool = DummyTool()

        with self._setup_deps(['foo']):
            self.assertFalse(tool.check_dependencies())

            # Make sure a second call produces the same results (since
            # a cache will be updated).
            self.assertFalse(tool.check_dependencies())

    @contextmanager
    def _setup_deps(cls, filenames=[], set_path=True):
        """Set up an environment for dependency checks.

        Args:
            filenames (list of unicode, optional):
                A list of executable filenames to write to the tmep directory.

            set_path (bool, optional):
                Whether to set the :envvar:`PATH` environment variable.

        Context:
            unicode:
            The generated temp directory.
        """
        tempdir = tempfile.mkdtemp()

        for filename in filenames:
            filename = os.path.join(tempdir, filename)

            with open(filename, 'w'):
                pass

            os.chmod(filename, 0o755)

        old_path = os.environ['PATH']

        if set_path:
            os.environ['PATH'] = tempdir

        try:
            yield tempdir
        finally:
            os.environ['PATH'] = old_path
            shutil.rmtree(tempdir)
