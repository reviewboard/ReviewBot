"""Review Bot tool to run rubocop."""

from __future__ import unicode_literals

import json

from reviewbot.config import config
from reviewbot.tools.base import BaseTool
from reviewbot.utils.process import execute
from reviewbot.utils.text import split_comma_separated


class RubocopTool(BaseTool):
    """Review Bot tool to run rubocop."""

    name = 'RuboCop'
    version = '1.0'
    description = (
        'Checks Ruby code for style errors based on the community Ruby style '
        'guide using RuboCop.'
    )
    timeout = 60

    exe_dependencies = ['rubocop']
    file_patterns = ['*.rb']

    options = [
        {
            'name': 'except',
            'field_type': 'django.forms.CharField',
            'default': '',
            'field_options': {
                'label': 'Except',
                'help_text': (
                    'Run all cops enabled by configuration except the '
                    'specified cop(s) and/or departments. This will be '
                    'passed to the --except command line argument (e.g. '
                    'Lint/UselessAssignment).'
                ),
                'required': False,
            },
        },
    ]

    def build_base_command(self, **kwargs):
        """Build the base command line used to review files.

        Args:
            **kwargs (dict, unused):
                Additional keyword arguments.

        Returns:
            list of unicode:
            The base command line.
        """
        settings = self.settings
        except_list = split_comma_separated(settings.get('except', '').strip())

        cmdline = [
            config['exe_paths']['rubocop'],
            '--format=json',
            '--display-style-guide',
        ]

        if except_list:
            cmdline.append('--except=%s' % ','.join(except_list))

        return cmdline

    def handle_file(self, f, path, base_command, **kwargs):
        """Perform a review of a single file.

        Args:
            f (reviewbot.processing.review.File):
                The file to process.

            path (unicode):
                The local path to the patched file to review.

            base_command (list of unicode):
                The base command used to run rubocop.

            **kwargs (dict, unused):
                Additional keyword arguments.
        """
        output = execute(base_command + [path],
                         ignore_errors=True)

        try:
            results = json.loads(output)
        except ValueError:
            # There's an error here. It *should* be in the first line.
            # Subsequent lines may contain stack traces or mostly-empty
            # result JSON payloads.
            lines = output.splitlines()

            f.comment('RuboCop could not analyze this file, due to the '
                      'following errors:\n'
                      '\n'
                      '```%s```'
                      % lines[0].strip(),
                      first_line=None,
                      rich_text=True)
            return

        if results['summary']['offense_count'] > 0:
            for offense in results['files'][0]['offenses']:
                cop_name = offense['cop_name']
                message = offense['message']
                location = offense['location']

                # Strip away the cop name prefix, if found.
                prefix = '%s: ' % cop_name

                if message.startswith(prefix):
                    message = message[len(prefix):]

                # Check the old and new fields, for compatibility.
                first_line = location.get('start_line', location['line'])
                last_line = location.get('last_line', location['line'])
                start_column = location.get('start_column', location['column'])

                f.comment(message,
                          first_line=first_line,
                          num_lines=last_line - first_line + 1,
                          start_column=start_column,
                          severity=offense.get('severity'),
                          error_code=cop_name,
                          rich_text=True)
