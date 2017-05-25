from __future__ import unicode_literals

from reviewbot.tools import Tool
from reviewbot.utils.process import execute, is_exe_in_path


class PyflakesTool(Tool):
    """Review Bot tool to run pyflakes."""

    name = 'Pyflakes'
    version = '1.0'
    description = 'Checks Python code for errors using Pyflakes.'
    timeout = 30

    def check_dependencies(self):
        """Verify the tool's dependencies are installed.

        Returns:
            bool:
            True if all dependencies for the tool are satisfied. If this
            returns False, the worker will not listen for this Tool's queue,
            and a warning will be logged.
        """
        return is_exe_in_path('pyflakes')

    def handle_file(self, f, settings):
        """Perform a review of a single file.

        Args:
            f (reviewbot.processing.review.File):
                The file to process.

            settings (dict):
                Tool-specific settings.
        """
        if not f.dest_file.endswith('.py'):
            # Ignore the file.
            return

        path = f.get_patched_file_path()

        if not path:
            return

        output = execute(
            [
                'pyflakes',
                path,
            ],
            split_lines=True,
            ignore_errors=True)

        for line in output:
            parsed = line.split(':', 2)
            lnum = int(parsed[1])
            msg = parsed[2]
            f.comment('%s' % (msg, ), lnum)
