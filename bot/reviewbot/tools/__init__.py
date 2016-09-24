from __future__ import unicode_literals


class Tool(object):
    """The base class all Review Bot tools should inherit from.

    This class provides base functionality specific to tools which
    process each file separately. If a tool would like to perform a
    different style of analysis, it may override the 'handle_files'
    method.
    """

    name = 'Tool'
    description = ''
    version = '1'
    options = []

    def __init__(self):
        pass

    def check_dependencies(self):
        """Verify the tool's dependencies are installed.

        requires is missing, otherwise it should return True. This can
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
        self.review = review
        self.settings = settings
        self.processed_files = set()
        self.ignored_files = set()

        self.handle_files(review.files)
        self.post_process(review)

    def handle_files(self, files):
        """Perform a review of each file."""
        for f in files:
            if self.handle_file(f):
                self.processed_files.add(f.dest_file)
            else:
                self.ignored_files.add(f.dest_file)

    def handle_file(self, f):
        """Perform a review of a single file.

        This method should be overridden by a Tool to execute its static
        analysis.

        Args:
            f (reviewbot.processing.review.File):
                The file to process.

        Returns:
            bool:
            Whether the tool executed successfully on the file.
        """
        return False

    def post_process(self, review):
        """Modify the review after the tool has completed.

        Unless overridden this will prepend some useful information
        about the tool execution to the 'body_top' of the review.

        Args:
            review (reviewbot.processing.review.Review):
                The review object.
        """
        header = '\n'.join(
            [
                'This is a review from Review Bot.',
                'Tool: %s' % self.name,
                '  Processed Files:',
            ] + [
                '    %s' % f
                for f in self.processed_files
            ] + [
                '  Ignored Files:',
            ] + [
                '    %s' % f
                for f in self.ignored_files
            ])

        review.body_top = '%s\n%s' % (header, review.body_top)
