"""Base support for creating code checking tools."""

from __future__ import unicode_literals

import logging
import os

from reviewbot.utils.filesystem import chdir, ensure_dirs_exist


class Tool(object):
    """The base class all Review Bot tools should inherit from.

    This class provides base functionality specific to tools which
    process each file separately.

    Most tools will override :py:meth:`handle_file`, performing a code review
    on the provided file.

    If a tool would like to perform a different style of analysis, it can
    override :py:meth:`handle_files`.
    """

    #: The displayed name of the tool.
    #:
    #: Type:
    #:     unicode
    name = ''

    #: A short description of the tool.
    #:
    #: Type:
    #:     unicode
    description = ''

    #: The compatibility version of the tool.
    #:
    #: This should only be changed for major breaking updates. It will break
    #: compatibility with existing integration configurations, requiring
    #: manual updates to those configurations. Any existing configurations
    #: referencing the old version will not be run, unless an older version
    #: of the tool is being handled through another Review Bot worker providing
    #: the older tool.
    #:
    #: Type:
    #:     unicode
    version = '1'

    #: Configurable options defined for the tool.
    #:
    #: Each item in the list is a dictionary representing a form field to
    #: display in the Review Board administration UI. Keys include:
    #:
    #: ``field_type`` (:py:class:`unicode`):
    #:     The full path as a string to a Django form field class to render.
    #:
    #: ``name`` (:py:class:`unicode`):
    #:     The name/ID of the field. This will map to the key in the
    #:     settings provided to :py:meth:`handle_files` and
    #:     :py:meth:`handle_file`.
    #:
    #: ``default`` (:py:class:`object`, optional):
    #:     The default value for the field.
    #:
    #: ``field_options`` (:py:class:`dict`, optional):
    #:     Additional options to pass to the form field's constructor.
    #:
    #: ``widget`` (:py:class:`dict`, optional):
    #:     Information on the Django form field widget class used to render
    #:     the field. This dictionary includes the following keys:
    #:
    #:     ``type`` (:py:class:`unicode`):
    #:         The full path as a string to a Django form field widget class.
    #:
    #:     ``attrs`` (:py:class:`dict`, optional):
    #:         A dictionary of attributes passed to the widget's constructor.
    #:
    #: Type:
    #:     list
    options = []

    #: Whether this tool requires a full checkout and working directory to run.
    #:
    #: Type:
    #:     bool
    working_directory_required = False

    #: Timeout for tool execution, in seconds.
    #:
    #: Type:
    #:     int
    timeout = None

    def __init__(self):
        """Initialize the tool."""
        self.output = None

    def check_dependencies(self):
        """Verify the tool's dependencies are installed.

        Subclasses should implement this to check for scripts or external
        programs the tool assumes exist on the path.

        Returns:
            bool:
            True if all dependencies for the tool are satisfied. If this
            returns False, the worker will not listen for this Tool's queue,
            and a warning will be logged.
        """
        return True

    def execute(self, review, settings={}, repository=None,
                base_commit_id=None):
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
        self.handle_files(review.files, settings)

    def handle_files(self, files, settings):
        """Perform a review of all files.

        This may be overridden by subclasses for tools that process all files
        at once.

        Args:
            files (list of reviewbot.processing.review.File):
                The files to process.

            settings (dict):
                Tool-specific settings.
        """
        for f in files:
            self.handle_file(f, settings)

    def handle_file(self, f, settings):
        """Perform a review of a single file.

        This method may be overridden by subclasses to process an individual
        file.

        Args:
            f (reviewbot.processing.review.File):
                The file to process.

            settings (dict):
                Tool-specific settings.
        """
        pass


class RepositoryTool(Tool):
    """Tool base class for tools that need access to the entire repository."""

    working_directory_required = True

    def execute(self, review, settings={}, repository=None,
                base_commit_id=None):
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
                logging.info('Patching %s', f.dest_file)

                ensure_dirs_exist(os.path.abspath(f.dest_file))

                with open(f.dest_file, 'wb') as fp:
                    fp.write(f.patched_file_contents)

                f.patched_file_path = f.dest_file

            # Now run the tool for everything.
            self.handle_files(review.files, settings)
