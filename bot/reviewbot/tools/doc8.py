"""Review Bot tool to run doc8."""

from __future__ import unicode_literals

import logging

from reviewbot.tools import Tool
from reviewbot.utils.process import execute, is_exe_in_path


class Doc8Tool(Tool):
    """Review Bot tool to run doc8."""

    name = 'doc8'
    version = '1.0'
    description = 'Checks reStructuredText for style.'
    timeout = 30
    options = [
        {
            'name': 'max_line_length',
            'field_type': 'django.forms.IntegerField',
            'default': 79,
            'field_options': {
                'label': 'Maximum Line Length',
                'help_text': 'The maximum line length to allow.',
                'required': True,
            },
        },
        {
            'name': 'encoding',
            'field_type': 'django.forms.CharField',
            'default': 'utf-8',
            'field_options': {
                'label': 'Encoding',
                'help_text': 'Encoding used for rst files.',
                'required': True,
            },
        },
    ]

    def check_dependencies(self):
        """Verify that the tool's dependencies are installed.

        Returns:
            bool:
            True if all dependencies for the tool are satisfied. If this
            returns False, the worker will not be listed for this Tool's queue,
            and a warning will be logged.
        """
        return is_exe_in_path('doc8')

    def handle_file(self, f, settings):
        """Perform a review of a single file.

        Args:
            f (reviewbot.processing.review.File):
                The file to process.

            settings (dict):
                Tool-specific settings.
        """
        if not f.dest_file.lower().endswith('.rst'):
            # Ignore the file.
            return

        path = f.get_patched_file_path()

        if not path:
            return

        output = execute(
            [
                'doc8', '-q',
                '--max-line-length=%s' % settings['max_line_length'],
                '--file-encoding=%s' % settings['encoding'],
                path,
            ],
            split_lines=True,
            ignore_errors=True)

        for line in output:
            try:
                # Strip off the filename, since it might have colons in it.
                line = line[len(path) + 1:]
                line_num, message = line.split(':', 1)
                f.comment(message.strip(), int(line_num))
            except Exception:
                logging.error('Cannot parse line with doc8: %s', line)
