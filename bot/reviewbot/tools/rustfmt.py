"""Review Bot tool to run rustfmt."""

from __future__ import unicode_literals

import re

from reviewbot.config import config
from reviewbot.tools.base import BaseTool
from reviewbot.utils.process import execute


class RustfmtTool(BaseTool):
    """Review Bot tool to run rustfmt."""

    name = 'rust fmt'
    version = '1.0'
    description = 'Checks that Rust code style matches rustfmt.'
    timeout = 30

    exe_dependencies = ['rustfmt']
    file_patterns = ['*.rs']

    ERROR_RE = re.compile(
        r'^error: (?P<text>.*)\n'
        r' --> .*?:(?P<linenum>\d+):(?P<column>\d+)$',
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
            config['exe_paths']['rustfmt'],
            '-q',
            '--check',
            '--color=never',
        ]

    def handle_file(self, f, path, base_command, **kwargs):
        """Perform a review of a single file.

        Args:
            f (reviewbot.processing.review.File):
                The file to process.

            path (unicode):
                The local path to the patched file to review.

            base_command (list of unicode):
                The base command used to run rustfmt.

            **kwargs (dict, unused):
                Additional keyword arguments.
        """
        output, errors = execute(base_command + [path],
                                 ignore_errors=True,
                                 return_errors=True)

        if errors:
            # The .rs file was likely unable to be parsed. Look for any
            # errors.
            for m in self.ERROR_RE.finditer(errors):
                f.comment(text=m.group('text'),
                          first_line=int(m.group('linenum')),
                          start_column=int(m.group('column')))
        elif output:
            f.comment('This file contains formatting errors and should be '
                      'run through `rustfmt`.',
                      first_line=None,
                      rich_text=True)
