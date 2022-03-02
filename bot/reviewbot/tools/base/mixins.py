"""Useful mixins for code checking tools.

Version Added:
    3.0
"""

from __future__ import unicode_literals

import os
import re

from reviewbot.config import config
from reviewbot.utils.filesystem import chdir, ensure_dirs_exist
from reviewbot.utils.process import execute
from reviewbot.utils.text import split_comma_separated


# Python 3.4+ includes glob.escape, but older versions do not. Optimistically,
# we'll use glob.escape, and we'll fall back on a custom implementation.
try:
    from glob import escape as glob_escape
except ImportError:
    _glob_escape_pattern = re.compile(r'([*?[])')

    def glob_escape(path):
        drive, path = os.path.split(path)

        return '%s%s' % (drive, _glob_escape_pattern.sub(r'[\1]', path))


class FilePatternsFromSettingMixin(object):
    """Mixin to set file patterns based on a configured tool setting.

    Subclasses can base file patterns off either a setting representing
    a comma-separated list of file patterns, or a setting representing a
    comma-separated list of file extensions. If both are provided, both will
    be checked, with the file patterns taking precedence over file extensions.

    If neither are provided by the user, the default list of file patterns
    set by the subclass (if any) will be used.

    Version Added:
        3.0
    """

    #: The name of a tool setting for a comma-separated list of extensions.
    #:
    #: Type:
    #:     unicode
    file_extensions_setting = None

    #: The name of a tool setting for a comma-separated list of patterns.
    #:
    #: Type:
    #:     unicode
    file_patterns_setting = None

    #: Whether to include default file patterns in the resulting list.
    #:
    #: Type:
    #:     boolean
    include_default_file_patterns = True

    def __init__(self, **kwargs):
        """Initialize the tool.

        Args:
            **kwargs (dict):
                Keyword arguments for the tool.
        """
        super(FilePatternsFromSettingMixin, self).__init__(**kwargs)

        settings = self.settings
        file_patterns = None

        if self.file_patterns_setting:
            value = settings.get(self.file_patterns_setting, '').strip()

            if value:
                file_patterns = split_comma_separated(value)

        if not file_patterns and self.file_extensions_setting:
            value = settings.get(self.file_extensions_setting, '').strip()

            file_patterns = [
                '*.%s' % glob_escape(ext.lstrip('.'))
                for ext in split_comma_separated(value)
            ]

        if file_patterns:
            if self.include_default_file_patterns and self.file_patterns:
                file_patterns += self.file_patterns

            self.file_patterns = [
                file_pattern
                for file_pattern in sorted(set(file_patterns))
                if file_pattern
            ]


class FullRepositoryToolMixin(object):
    """Mixin for tools that need access to the entire repository.

    This will take care of checking out a copy of the repository and applying
    patches from the diff being reviewed.

    Version Added:
        3.0:
        This replaced the legacy :py:class:`reviewbot.tools.RepositoryTool`.
    """

    working_directory_required = True

    def execute(self, review, repository=None, base_commit_id=None, **kwargs):
        """Perform a review using the tool.

        Args:
            review (reviewbot.processing.review.Review):
                The review object.

            settings (dict, optional):
                Tool-specific settings.

            repository (reviewbot.repositories.Repository, optional):
                The repository.

            base_commit_id (unicode, optional):
                The ID of the commit that the patch should be applied to.
        """
        repository.sync()
        working_dir = repository.checkout(base_commit_id)

        # Patch all the files first.
        with chdir(working_dir):
            for f in review.files:
                self.logger.debug('Patching %s', f.dest_file)
                f.apply_patch(working_dir)

            # Now run the tool for everything.
            super(FullRepositoryToolMixin, self).execute(review, **kwargs)


class JavaToolMixin(object):
    """Mixin for Java-based tools.

    Version Added:
        3.0
    """

    #: Main class to call to run the Java application.
    #:
    #: Type:
    #:     unicode
    java_main = None

    #: The key identifying the classpaths to use.
    #:
    #: Type:
    #:     unicode
    java_classpaths_key = None

    exe_dependencies = ['java']

    @classmethod
    def set_has_java_runtime(cls, has_runtime):
        """Set whether there's a Java runtime installed.

        Args:
            has_runtime (bool):
                Whether there's a runtime installed.
        """
        JavaToolMixin._has_java_runtime = has_runtime

    @classmethod
    def clear_has_java_runtime(cls):
        """Clear whether there's a Java runtime installed.

        This will force the next dependency check to re-check for a runtime.
        """
        try:
            delattr(JavaToolMixin, '_has_java_runtime')
        except AttributeError:
            pass

    def check_dependencies(self):
        """Verify the tool's dependencies are installed.

        This will invoke the base class's dependency checking, ensuring that
        :command:`java` is available, and will then attempt to run the
        configured Java class (:py:attr:`java_main`), checking that it could
        be found.

        Returns:
            bool:
            True if all dependencies for the tool are satisfied. If this
            returns False, the worker will not listen for this Tool's queue,
            and a warning will be logged.
        """
        # Run any standard dependency checks.
        if not super(JavaToolMixin, self).check_dependencies():
            return False

        # Make sure that `java` has a suitable runtime. It's not enough
        # to just be present in the path.
        if not hasattr(JavaToolMixin, '_has_java_runtime'):
            try:
                execute([config['exe_paths']['java'], '-version'])

                JavaToolMixin.set_has_java_runtime(True)
            except Exception:
                JavaToolMixin.set_has_java_runtime(False)

        if not JavaToolMixin._has_java_runtime:
            return False

        # If there's a classpath set, make sure the modules we need are in it.
        if self.java_classpaths_key is not None:
            classpath = \
                config['java_classpaths'].get(self.java_classpaths_key, [])

            if not self._check_java_classpath(classpath):
                return False

        # If this tool is invoked directly through Java with a Main class,
        # check it now.
        if self.java_main:
            output = execute(self._build_java_command(),
                             ignore_errors=True)

            return 'Could not find or load main class' not in output

        return True

    def build_base_command(self, **kwargs):
        """Build the base command line used to review files.

        Args:
            **kwargs (dict, unused):
                Additional keyword arguments.

        Returns:
            list of unicode:
            The base command line.
        """
        return self._build_java_command(**kwargs)

    def _build_java_command(self):
        """Return the base Java command for running the class.

        This will build the class path and command line for running
        :py:attr:`java_main`.

        Returns:
            list of unicode:
            The base command line for running the Java class.
        """
        classpath = ':'.join(
            config['java_classpaths'].get(self.java_classpaths_key, []))

        cmdline = [config['exe_paths']['java']]

        if classpath:
            cmdline += ['-cp', classpath]

        cmdline.append(self.java_main)

        return cmdline

    def _check_java_classpath(self, classpath):
        """Return whether all entries in a classpath exist.

        Args:
            classpath (list of unicode):
                The classpath locations.

        Returns:
            bool:
            ``True`` if all entries exist on the filesystem. ``False`` if
            one or more are missing.
        """
        if not classpath:
            return False

        for path in classpath:
            if not path or not os.path.exists(path):
                return False

        return True
