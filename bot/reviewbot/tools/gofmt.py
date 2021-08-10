"""Review Bot tool to run go fmt."""

from __future__ import unicode_literals

import re

from reviewbot.config import config
from reviewbot.tools.base import BaseTool
from reviewbot.utils.process import execute


class GofmtTool(BaseTool):
    """Review Bot tool to run go fmt."""

    name = 'go fmt'
    version = '1.0'
    description = 'Checks code for styling using "go fmt".'
    timeout = 30

    exe_dependencies = ['go']
    file_patterns = ['*.go']

    ERROR_RE = re.compile(
        r'^(.*\.go):(?P<linenum>\d+):(?P<column>\d+): (?P<text>.*)$',
        re.M)

    def build_base_command(self, **kwargs):
        """Build the base command line used to review files.

        Args:
            **kwargs (dict, unused):
                Additional keyword arguments.

        Returns:
            list of unicode:
            The base command line.
        """
        return [
            config['exe_paths']['go'],
            'fmt',
        ]

    def handle_file(self, f, path, base_command, **kwargs):
        """Perform a review of a single file.

        Args:
            f (reviewbot.processing.review.File):
                The file to process.

            path (unicode):
                The local path to the patched file to review.

            base_command (list of unicode):
                The base command used to run pyflakes.

            **kwargs (dict, unused):
                Additional keyword arguments.
        """
        output, errors = execute(base_command + [path],
                                 ignore_errors=True,
                                 return_errors=True)

        if errors:
            # The .go file was likely unable to be parsed. Look for any
            # errors.
            for m in self.ERROR_RE.finditer(errors):
                f.comment(text=m.group('text'),
                          first_line=int(m.group('linenum')),
                          start_column=int(m.group('column')))
        elif output:
            f.comment('This file contains formatting errors and should be '
                      'run through `go fmt`.',
                      first_line=None,
                      rich_text=True)
