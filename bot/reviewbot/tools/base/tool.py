"""Base support for creating code checking tools."""

from __future__ import unicode_literals

from fnmatch import fnmatchcase

from reviewbot.config import config
from reviewbot.utils.log import get_logger
from reviewbot.utils.process import is_exe_in_path


class BaseTool(object):
    """The base class all Review Bot tools should inherit from.

    This class provides base functionality specific to tools which
    process each file separately.

    Most tools will override :py:meth:`handle_file`, performing a code review
    on the provided file.

    If a tool would like to perform a different style of analysis, it can
    override :py:meth:`handle_files`.

    Attributes:
        settings (dict):
            Settings configured for this tool in Review Board, based on
            :py:attr:`options`.
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

    #: A list of executable tools required by the tool.
    #:
    #: Each is the name of an executable on the filesystem, either in the
    #: :envvar:`PATH` or defined in the ``exe_paths`` configuration.
    #:
    #: These will be checked when the worker starts. If a dependency for a
    #: tool is missing, the worker will not enable it.
    #:
    #: Version Added:
    #:     3.0:
    #:     Tools that previously implemented :py:meth:`check_dependencies`
    #:     may want to be updated to use this.
    #:
    #: Type:
    #:     dict
    exe_dependencies = []

    #: A list of filename patterns this tool can process.
    #:
    #: This is intended for tools that have a fixed list of file extensions
    #: or specific filenames they should process. Each entry is a
    #: glob file pattern (e.g., ``*.py``, ``.config/*.xml``, ``dockerfile``,
    #: etc.), and must be lowercase (as filenames will be normalized to
    #: lowercase for comparison). See :py:mod:`fnmatch` for pattern rules.
    #:
    #: Tools can leave this empty to process all files, or can override
    #: :py:meth:`get_can_handle_file` to implement custom logic (e.g., basing
    #: matching off a tool's settings, or providing case-sensitive matches).
    #:
    #: Version Added:
    #:     3.0
    #:
    #: Type:
    #:     list of unicode
    file_patterns = []

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

    def __init__(self, settings=None, **kwargs):
        """Initialize the tool.

        Version Changed:
            3.0:
            Added ``settings`` and ``**kwargs`` arguments. Subclasses must
            provide this by Review Bot 4.0.

        Args:
            settings (dict, optional):
                Settings provided to the tool.

            **kwargs (dict):
                Additional keyword arguments, for future expansion.
        """
        self.settings = settings or {}
        self.output = None
        self._logger = None

    @property
    def logger(self):
        """The logger for the tool.

        This logger will contain information on the process, the task (if
        it's running in a task), and the tool name.

        Version Added:
            3.0

        Type:
            logging.Logger
        """
        if self._logger is None:
            from reviewbot.celery import get_celery

            self._logger = get_logger(
                self.name,
                is_task_logger=get_celery().current_task is not None)

        return self._logger

    def check_dependencies(self, **kwargs):
        """Verify the tool's dependencies are installed.

        By default, this will check :py:attr:`exe_dependencies`, ensuring each
        is available to the tool.

        For each entry in :py:attr:`exe_dependencies`, :envvar:`PATH` will be
        checked. If the dependency name is found in the ``exe_paths`` mapping
        in the Review Bot configuration, that path will be checked.

        Subclasses can implement this if they need more advanced checks.

        Args:
            **kwargs (dict, unused):
                Additional keyword arguments. This is intended for future
                expansion.

        Returns:
            bool:
            True if all dependencies for the tool are satisfied. If this
            returns False, the worker will not listen for this Tool's queue,
            and a warning will be logged.
        """
        exe_paths = config['exe_paths']

        for exe in self.exe_dependencies:
            path = exe_paths.get(exe, exe)

            if not path or not is_exe_in_path(path, cache=exe_paths):
                return False

        return True

    def get_can_handle_file(self, review_file, **kwargs):
        """Return whether this tool can handle a given file.

        By default, this checks the full path of the destination file against
        the patterns in :py:attr:`file_patterns`. If the file path matches, or
        that list is empty, this will allow the file to be handled.

        Subclasses can override this to provide custom matching logic.

        Version Added:
            3.0

        Args:
            review_file (reviewbot.processing.review.File):
                The file to check.

            **kwargs (dict, unused):
                Additional keyword arguments passed to :py:meth:`execute`.
                This is intended for future expansion.

        Returns:
            bool:
            ``True`` if the file can be handled. ``False`` if it cannot.
        """
        if not self.file_patterns:
            return True

        filename = review_file.dest_file.lower()

        for pattern in self.file_patterns:
            if fnmatchcase(filename, pattern):
                return True

        return False

    def execute(self, review, repository=None, base_commit_id=None, **kwargs):
        """Perform a review using the tool.

        Version Changed:
            3.0:
            ``settings`` is deprecated in favor of the :py:attr:`settings`
            attribute on the instance. It's still provided in 3.0.

            ``**kwargs`` is now expected.

        Args:
            review (reviewbot.processing.review.Review):
                The review object.

            repository (reviewbot.repositories.Repository, optional):
                The repository.

            base_commit_id (unicode, optional):
                The ID of the commit that the patch should be applied to.

            **kwargs (dict, unused):
                Additional keyword arguments, for future expansion.
        """
        if not getattr(self, 'legacy_tool', False):
            kwargs.update({
                'base_command': self.build_base_command(),
                'review': review,
            })

        self.handle_files(review.files, **kwargs)

    def build_base_command(self, **kwargs):
        """Build the base command line used to review files.

        This will be passed to :py:meth:`handle_file` for each file. It's
        useful for constructing a common command line and arguments that
        will apply to each file in a diff.

        Version Added:
            3.0

        Args:
            **kwargs (dict, unused):
                Additional keyword arguments, for future expansion.

        Returns:
            list of unicode:
            The base command line.
        """
        return []

    def handle_files(self, files, **kwargs):
        """Perform a review of all files.

        This may be overridden by subclasses for tools that process all files
        at once.

        Version Changed:
            3.0:
            ``settings`` is deprecated in favor of the :py:attr:`settings`
            attribute on the instance. It's still provided in 3.0.

            ``**kwargs`` is now expected.

            These will be enforced in Review Bot 4.0.

        Args:
            files (list of reviewbot.processing.review.File):
                The files to process.

            **kwargs (dict):
                Additional keyword arguments passed to :py:meth:`execute`.
                This is intended for future expansion.
        """
        legacy_tool = getattr(self, 'legacy_tool', False)

        for f in files:
            if self.get_can_handle_file(review_file=f, **kwargs):
                if legacy_tool:
                    self.handle_file(f, **kwargs)
                else:
                    path = f.get_patched_file_path()

                    if path:
                        self.handle_file(f, path=path, **kwargs)

    def handle_file(self, f, path=None, base_command=None, **kwargs):
        """Perform a review of a single file.

        This method may be overridden by subclasses to process an individual
        file.

        Version Changed:
            3.0:
            ``settings`` is deprecated in favor of the :py:attr:`settings`
            attribute on the instance. It's still provided in 3.0.

            ``path`` is added, which is the result of a
            :py:meth:`~reviewbot.processing.File.get_patched_file_path`
            command, and must be valid for this method to be called.

            ``base_command`` is added, which would be the result of
            :py:meth:`build_base_command`.

            ``**kwargs`` is now expected.

            These will be enforced in Review Bot 4.0.

        Args:
            f (reviewbot.processing.review.File):
                The file to process.

            path (unicode, optional):
                The local path to the patched file to review.

                This won't be passed for legacy tools.

            base_command (list of unicode, optional):
                The common base command line used for reviewing a file,
                if returned from :py:meth:`build_base_command`.

            **kwargs (dict):
                Additional keyword arguments passed to :py:meth:`handle_files`.
                This is intended for future expansion.
        """
        pass
