"""Base test case support for tools.

Version Added:
    3.0
"""

from __future__ import unicode_literals

import os
import tempfile
from copy import deepcopy
from functools import wraps
from unittest import SkipTest

import kgb
import six

from reviewbot.config import config
from reviewbot.repositories import GitRepository
from reviewbot.testing import TestCase
from reviewbot.utils.filesystem import make_tempdir
from reviewbot.utils.process import execute


class ToolTestCaseMetaclass(type):
    """Metaclass for tool tests.

    This is required for all subclasses of :py:class:`BaseToolTestCase`.

    This will split any test methods that are marked as a simulation and/or
    integration test into individual tests, set up by the subclass's
    :py:meth:`~BaseToolTestCase.setup_simulation_test` or
    :py:meth:`~BaseToolTestCase.setup_integration_test` method.

    Version Added:
        3.0
    """

    def __new__(meta, name, bases, d):
        """Construct a new class.

        Args:
            name (str):
                The name of the class.

            bases (tuple of str):
                The parent classes/mixins.

            d (dict):
                The class dictionary.

        Returns:
            type:
            The new class.
        """
        tool_class = d.get('tool_class')

        assert tool_class, '%s must set base_tool_class' % name

        if tool_class.exe_dependencies:
            assert d.get('tool_exe_config_key'), \
               '%s must set tool_exe_config_key' % name
            assert d.get('tool_exe_path'), '%s must set tool_exe_path' % name

        for func_name, func in six.iteritems(d.copy()):
            if callable(func):
                added = False

                if hasattr(func, 'integration_setup_kwargs'):
                    new_name = meta.tag_func_name(func_name, 'integration')
                    d[new_name] = meta.make_integration_test_func(func,
                                                                  new_name)
                    added = True

                if hasattr(func, 'simulation_setup_kwargs'):
                    new_name = meta.tag_func_name(func_name, 'simulation')
                    d[new_name] = meta.make_simulation_test_func(func,
                                                                 new_name)
                    added = True

                if added:
                    del d[func_name]

        return super(ToolTestCaseMetaclass, meta).__new__(meta, name, bases, d)

    @classmethod
    def tag_func_name(meta, func_name, tag):
        """Return a function name tagged with an identifier.

        This will convert a ``test_*`` function name into a
        :samp:`test_{tag}_*`.

        Args:
            func_name (str):
                The original name of the function.

            tag (unicode):
                The tag to add.

        Returns:
            str:
            The resulting function name.
        """
        assert func_name.startswith('test_')
        return str('test_%s_%s' % (tag, func_name[5:]))

    @classmethod
    def make_integration_test_func(meta, func, func_name):
        """Return a new function for an integration test.

        The function will wrap the original function from the class, and
        set up the state for an integration test.

        Args:
            func (callable):
                The function to wrap.

            func_name (str):
                The name of the function.

        Returns:
            callable:
            The new integration test function.
        """
        @wraps(func)
        def _wrapper(self, *args, **kwargs):
            old_path = os.environ['PATH']
            old_tool_exe_path = self.tool_exe_path

            try:
                os.environ['PATH'] = self._old_path

                if not self.tool_class().check_dependencies():
                    raise SkipTest('%s dependencies not available'
                                   % self.tool_class.name)

                if self.tool_exe_config_key:
                    self.tool_exe_path = \
                        config['exe_paths'][self.tool_exe_config_key]

                self.spy_on(execute)
                self.setup_integration_test(**func.integration_setup_kwargs)

                return func(self, *args, **kwargs)
            finally:
                os.environ['PATH'] = old_path
                self.tool_exe_path = old_tool_exe_path

        _wrapper.__name__ = func_name
        _wrapper.__doc__ = '%s [integration test]' % _wrapper.__doc__

        return _wrapper

    @classmethod
    def make_simulation_test_func(meta, func, func_name):
        """Return a new function for a simulation test.

        The function will wrap the original function from the class, and
        set up the state for a simulation test.

        Args:
            func (callable):
                The function to wrap.

            func_name (str):
                The name of the function.

        Returns:
            callable:
            The new simulation test function.
        """
        @wraps(func)
        def _wrapper(self, *args, **kwargs):
            print('setup!')
            self.setup_simulation_test(**func.simulation_setup_kwargs)

            return func(self, *args, **kwargs)

        _wrapper.__name__ = func_name
        _wrapper.__doc__ = '%s [simulation test]' % _wrapper.__doc__

        return _wrapper


class BaseToolTestCase(kgb.SpyAgency, TestCase):
    """Base class for Tool test cases.

    Version Added:
        3.0
    """

    #: The tool class to test.
    #:
    #: This is required.
    #:
    #: Type:
    #:     type
    tool_class = None

    #: The key in the configuration identifying the executable of the tool.
    #:
    #: This is required.
    #:
    #: Type:
    #:     unicode
    tool_exe_config_key = None

    #: The path to the executable for running the tool.
    #:
    #: This will generally be a fake path for simulated tool runs, but a
    #: real one for integration tests. It can be set on the class or during
    #: test/test suite setup.
    #:
    #: Type:
    #:     unicode
    tool_exe_path = None

    #: Extra executables needed to run the tool.
    #:
    #: If the tool needs more than one executable for executions or dependency
    #: checks, they should be placed here. Keys are equivalent to
    #: :py:attr:`tool_exe_config_key`, and values are equivalent to
    #: :py:attr:`tool_exe_path`.
    #:
    #: Type:
    #:     dict
    tool_extra_exe_paths = {}

    def run_get_can_handle_file(self, filename, file_contents=b'',
                                tool_settings={}):
        """Run get_can_handle_file with the given file and settings.

        This will create the review objects, set up a repository (if needed
        by the tool), apply any configuration, and run
        :py:meth:`~reviewbot.tools.base.BaseTool.get_can_handle_file`.

        Args:
            filename (unicode):
                The filename of the file being reviewed.

            file_contents (bytes, optional):
                File content to review.

            tool_settings (dict, optional):
                The settings to pass to the tool constructor.

        Returns:
            bool:
            ``True`` if the file can be handled. ``False`` if it cannot.
        """
        review = self.create_review()
        review_file = self.create_review_file(
            review,
            source_file=filename,
            dest_file=filename,
            diff_data=self.create_diff_data(chunks=[{
                'change': 'insert',
                'lines': file_contents.splitlines(),
                'new_linenum': 1,
            }]),
            patched_content=file_contents)

        tool = self.tool_class(settings=tool_settings)

        return tool.get_can_handle_file(review_file)

    def run_tool_execute(self, filename, file_contents, checkout_dir=None,
                         tool_settings={}, other_files={}):
        """Run execute with the given file and settings.

        This will create the review objects, set up a repository (if needed
        by the tool), apply any configuration, and run
        :py:meth:`~reviewbot.tools.base.BaseTool.execute`.

        Args:
            filename (unicode):
                The filename of the file being reviewed.

            file_contents (bytes):
                File content to review.

            checkout_dir (unicode, optional):
                An explicit directory to use as the checkout directory, for
                tools that require full-repository checkouts.

            tool_settings (dict, optional):
                The settings to pass to the tool constructor.

            other_files (dict, optional):
                Other files to write to the tree. Each will result in a new
                file added to the review.

                The dictionary is a map of file paths (relative to the
                checkout directory) to byte strings.

        Returns:
            tuple:
            A 2-tuple containing:

            1. The review (:py:class:`reviewbot.processing.review.Review)`
            2. The file entry corresponding to ``filename``
               (:py:class:`reviewbot.processing.review.File`)

            If ``other_files`` is specified, the second tuple item will
            instead be a dictionary of keys from ``other_files`` (along with
            ``filename``) to :py:class:`reviewbot.processing.review.File`
            instances.
        """
        if self.tool_class.working_directory_required:
            repository = GitRepository(name='MyRepo',
                                       clone_path='git://example.com/repo')
            self.spy_on(repository.sync, call_original=False)

            @self.spy_for(repository.checkout)
            def _checkout(_self, *args, **kwargs):
                return checkout_dir or make_tempdir()
        else:
            repository = None

        review = self.create_review()
        review_file = self.create_review_file(
            review,
            source_file=filename,
            dest_file=filename,
            diff_data=self.create_diff_data(chunks=[{
                'change': 'insert',
                'lines': file_contents.splitlines(),
                'new_linenum': 1,
            }]),
            patched_content=file_contents)

        review_files = {}

        if other_files:
            review_files[filename] = review_file

            for other_filename, other_contents in six.iteritems(other_files):
                review_files[other_filename] = self.create_review_file(
                    review,
                    source_file=other_filename,
                    dest_file=other_filename,
                    diff_data=self.create_diff_data(chunks=[{
                        'change': 'insert',
                        'lines': other_contents.splitlines(),
                        'new_linenum': 1,
                    }]),
                    patched_content=other_contents)

        worker_config = deepcopy(self.config)
        exe_paths = worker_config.setdefault('exe_paths', {})
        exe_paths.update({
            self.tool_exe_config_key: self.tool_exe_path,
        })

        if self.tool_extra_exe_paths:
            exe_paths.update(self.tool_extra_exe_paths)

        with self.override_config(worker_config):
            tool = self.tool_class(settings=tool_settings)
            tool.execute(review,
                         repository=repository)

        if other_files:
            return review, review_files

        return review, review_file

    def setup_integration_test(self, **kwargs):
        """Set up an integration test.

        Args:
            **kwargs (dict):
                Keyword arguments passed to
                :py:func:`~reviewbot.tools.testing.testcases.integration_test`.
        """
        pass

    def setup_simulation_test(self, **kwargs):
        """Set up a simulation test.

        Args:
            **kwargs (dict):
                Keyword arguments passed to
                :py:func:`~reviewbot.tools.testing.testcases.simulation_test`.
        """
        pass
