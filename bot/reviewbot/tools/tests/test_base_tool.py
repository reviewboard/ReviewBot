"""Unit tests for reviewbot.tools.BaseTool."""

from __future__ import unicode_literals

import os
import shutil
import tempfile
from contextlib import contextmanager

import kgb

from reviewbot.testing import TestCase
from reviewbot.tools import BaseTool, Tool


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

    def test_get_can_handle_file_with_empty_list(self):
        """Testing BaseTool.get_can_handle_file with empty list"""
        class PatternsTool(BaseTool):
            pass

        review = self.create_review()
        review_file = self.create_review_file(review)

        tool = PatternsTool()
        self.assertTrue(tool.get_can_handle_file(review_file, settings={}))

    def test_get_can_handle_file_with_matching_filename(self):
        """Testing BaseTool.get_can_handle_file with matching filename"""
        review = self.create_review()
        review_file1 = self.create_review_file(review,
                                               dest_file='/src/foo.c')
        review_file2 = self.create_review_file(review,
                                               dest_file='/src/bar.C')
        review_file3 = self.create_review_file(review,
                                               dest_file='/src/baz.hpp')

        class PatternsTool(BaseTool):
            file_patterns = ['*.c', '*.h*']

        tool = PatternsTool()
        self.assertTrue(tool.get_can_handle_file(review_file1, settings={}))
        self.assertTrue(tool.get_can_handle_file(review_file2, settings={}))
        self.assertTrue(tool.get_can_handle_file(review_file3, settings={}))

    def test_get_can_handle_file_without_matching_filename(self):
        """Testing BaseTool.get_can_handle_file without matching filename"""
        review = self.create_review()
        review_file1 = self.create_review_file(review,
                                               dest_file='/src/foo.c')
        review_file2 = self.create_review_file(review,
                                               dest_file='/inc/bar.cc')
        review_file3 = self.create_review_file(review,
                                               dest_file='/main.xml')

        class PatternsTool(BaseTool):
            file_patterns = ['/inc/*.c', '.*.xml']

        tool = PatternsTool()
        self.assertFalse(tool.get_can_handle_file(review_file1, settings={}))
        self.assertFalse(tool.get_can_handle_file(review_file2, settings={}))
        self.assertFalse(tool.get_can_handle_file(review_file3, settings={}))

    def test_handle_files_with_patched_file_none(self):
        """Testing BaseTool.handle_files with file.get_patched_file_path() as
        None
        """
        tool = DummyTool()

        review = self.create_review()
        review_file1 = self.create_review_file(review,
                                               dest_file='/src/foo.c')
        review_file2 = self.create_review_file(review,
                                               dest_file='/inc/bar.cc')

        self.spy_on(tool.handle_file)
        self.spy_on(review_file1.get_patched_file_path,
                    op=kgb.SpyOpReturn(None))
        self.spy_on(review_file2.get_patched_file_path)

        tool.handle_files(review.files)

        self.assertSpyCalled(review_file1.get_patched_file_path)
        self.assertSpyCalled(review_file2.get_patched_file_path)
        self.assertSpyCalledWith(tool.handle_file, review_file2)
        self.assertSpyCallCount(tool.handle_file, 1)

    def test_handle_files_with_patched_file_none_and_legacy_tool(self):
        """Testing BaseTool.handle_files with file.get_patched_file_path() as
        None and legacy tool
        """
        class LegacyTool(Tool):
            pass

        tool = LegacyTool()

        review = self.create_review()
        review_file1 = self.create_review_file(review,
                                               dest_file='/src/foo.c')
        review_file2 = self.create_review_file(review,
                                               dest_file='/inc/bar.cc')

        self.spy_on(tool.handle_file)
        self.spy_on(review_file1.get_patched_file_path,
                    op=kgb.SpyOpReturn(None))
        self.spy_on(review_file2.get_patched_file_path)

        tool.handle_files(review.files)

        self.assertSpyNotCalled(review_file1.get_patched_file_path)
        self.assertSpyNotCalled(review_file2.get_patched_file_path)
        self.assertSpyCalledWith(tool.handle_file, review_file1)
        self.assertSpyCalledWith(tool.handle_file, review_file2)
        self.assertSpyCallCount(tool.handle_file, 2)

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
