class Tool(object):
    """The base class all Review Bot tools should inherit from.

    This class provides base functionality specific to tools which
    process each file separately. If a tool would like to perform a
    different style of analysis, it may override the 'handle_files'
    method.
    """
    name = "Tool"
    description = ""
    version = "1"
    options = []

    def __init__(self):
        pass

    def check_dependencies(self):
        """Verify the tool's dependencies are installed.

        This method should return False if any dependency the tool
        requires is missing, otherwise it should return True. This can
        and should be used to check for scripts or external programs
        the tool assumes exist on the path.

        If False is returned, the worker will not listen on the Tool's
        queue, and a warning will be logged.
        """
        return True

    def execute(self, review, settings={}):
        """Perform a review using the tool."""
        self.review = review
        self.settings = settings
        self.processed_files = set()
        self.ignored_files = set()

        self.handle_files(review.files)
        self.post_process(review)

    def handle_files(self, files):
        """Perform a review of each file.

        Keeps track of which files were processed by the tool and
        which were ignored. 'handle_file' returns a True value to
        indicate it processed the file, any other return value
        indicates the file was ignored.
        """
        for f in files:
            if self.handle_file(f):
                self.processed_files.add(f.dest_file)
            else:
                self.ignored_files.add(f.dest_file)

    def handle_file(self, f):
        """Perform a review of a single file.

        This method should be overridden by a Tool to execute it's
        static analysis.
        """
        return False

    def post_process(self, review):
        """Modify the review after the tool has completed.

        Unless overridden this will prepend some useful information
        about the tool execution to the 'body_top' of the review.
        """
        header = "This is a review from Review Bot.\n"
        header += "  Tool: %s" % self.name
        header += "\n"
        header += "  Processed Files:"
        header += "\n"
        for f in self.processed_files:
            header += "    %s\n" % f

        header += "  Ignored Files:\n"
        for f in self.ignored_files:
            header += "    %s\n" % f

        review.body_top = "%s\n%s" % (header, review.body_top)
