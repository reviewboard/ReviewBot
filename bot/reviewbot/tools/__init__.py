from __future__ import unicode_literals


class Tool(object):
    """The base class all Review Bot tools should inherit from.

    This class provides base functionality specific to tools which
    process each file separately. If a tool would like to perform a
    different style of analysis, it may override the 'handle_files'
    method.
    """

    name = ''
    description = ''
    version = '1'
    options = []

    #: Timeout for tool execution, in seconds.
    timeout = None

    def __init__(self):
        pass

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

    def execute(self, review, settings={}):
        """Perform a review using the tool.

        Args:
            review (reviewbot.processing.review.Review):
                The review object.

            settings (dict):
                Tool-specific settings.
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
