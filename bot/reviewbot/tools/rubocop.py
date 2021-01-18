"""Review Bot tool to run rubocop."""

from __future__ import unicode_literals

import logging

from reviewbot.tools import Tool
from reviewbot.utils.process import execute, is_exe_in_path


logger = logging.getLogger(__name__)


class RubocopTool(Tool):
    """Review Bot tool to run rubocop."""

    name = 'RuboCop'
    version = '1.0'
    description = ('Checks Ruby code for style errors based on the '
                   'community Ruby style guide using RuboCop.')
    timeout = 60
    options = [
        {
            'name': 'except',
            'field_type': 'django.forms.CharField',
            'default': '',
            'field_options': {
                'label': 'Except',
                'help_text': ('Run all cops enabled by configuration except '
                              'the specified cop(s) and/or departments. This '
                              'will be passed to the --except command line '
                              'argument (e.g. Lint/UselessAssignment).'),
                'required': False,
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
        return is_exe_in_path('rubocop')

    def handle_file(self, f, settings):
        """Perform a review of a single file.

        Args:
            f (reviewbot.processing.review.File):
                The file to process.

            settings (dict):
                Tool-specific settings.
        """
        if not f.dest_file.lower().endswith('.rb'):
            # Ignore the file.
            return

        path = f.get_patched_file_path()

        if not path:
            return

        if settings['except'] != '':
            try:
                output = execute(
                    [
                        'rubocop',
                        '--except=%s' % settings['except'],
                        '--format=emacs',
                        path,
                    ],
                    split_lines=True,
                    ignore_errors=True)
            except Exception as e:
                logger.exception('RuboCop failed: %s', e)
        else:
            try:
                output = execute(
                    [
                        'rubocop',
                        '--format=emacs',
                        path,
                    ],
                    split_lines=True,
                    ignore_errors=True)
            except Exception as e:
                logger.exception('RuboCop failed: %s', e)

        for line in output:
            try:
                # Strip off the filename, since it might have colons in it.
                line = line[len(path) + 1:]
                line_num, column, message_type, message = line.split(':', 3)
                f.comment(message.strip(), int(line_num))
            except Exception as e:
                logger.exception('Cannot parse the rubocop output: %s', e)
