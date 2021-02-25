"""Review Bot tool to run go fmt."""

from __future__ import unicode_literals

import logging

from reviewbot.tools import Tool
from reviewbot.utils.process import execute, is_exe_in_path


logger = logging.getLogger(__name__)


class GofmtTool(Tool):
    """Review Bot tool to run go fmt."""

    name = 'go fmt'
    version = '1.0'
    description = ('Checks code for styling using built-in Go tools such as '
                   '"go fmt".')
    timeout = 30

    def check_dependencies(self):
        """Verify the tool's dependencies are installed.

        Returns:
            bool:
            True if all dependencies for the tool are satisfied. If this
            returns False, the worker will not listen for this Tool's queue,
            and a warning will be logged.
        """
        return is_exe_in_path('go')

    def handle_file(self, f, settings):
        """Perform a review of a single file.

        Args:
            f (reviewbot.processing.review.File):
                The file to process.

            settings (dict):
                Tool-specific settings.
        """
        if not f.dest_file.lower().endswith('.go'):
            # Ignore the file.
            return

        path = f.get_patched_file_path()

        if not path:
            return

        # Build and execute the go fmt command.
        try:
            gofmt_output = execute(['go', 'fmt', path])

            if gofmt_output:
                f.comment('This file contains formatting errors and should be '
                          'run through `go fmt`.',
                          first_line=None,
                          rich_text=True)
        except Exception as e:
            logger.exception('go fmt failed for the file: %s %s', path, e)
