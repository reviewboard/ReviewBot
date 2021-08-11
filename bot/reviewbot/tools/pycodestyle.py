"""Unit tests for reviewbot.tools.pycodestyle."""

from __future__ import unicode_literals

from reviewbot.config import config
from reviewbot.tools import BaseTool
from reviewbot.utils.process import execute


class PycodestyleTool(BaseTool):
    """Review Bot tool to run pycodestyle."""

    name = 'pycodestyle'
    version = '1.0'
    description = 'Checks Python code for style errors.'
    timeout = 30

    exe_dependencies = ['pycodestyle']
    file_patterns = ['*.py']

    options = [
        {
            'name': 'max_line_length',
            'field_type': 'django.forms.IntegerField',
            'default': 79,
            'field_options': {
                'label': 'Maximum line length',
                'help_text': (
                    'The maximum length allowed for lines. Any lines longer '
                    'than this length will cause an issue to be filed.'
                ),
                'required': True,
            },
        },
        {
            'name': 'ignore',
            'field_type': 'django.forms.CharField',
            'default': '',
            'field_options': {
                'label': 'Ignore',
                'help_text': (
                    'A comma-separated list of errors and warnings to '
                    'ignore. This will be passed to the --ignore command '
                    'line argument (e.g. E4,W).'
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
        ignore = settings.get('ignore', '').strip()

        cmd = [
            config['exe_paths']['pycodestyle'],
            '--max-line-length=%s' % settings['max_line_length'],
            '--format=%(code)s:%(row)d:%(col)d:%(text)s',
        ]

        if ignore:
            cmd.append('--ignore=%s' % ignore)

        return cmd

    def handle_file(self, f, path, base_command, **kwargs):
        """Perform a review of a single file.

        Args:
            f (reviewbot.processing.review.File):
                The file to process.

            path (unicode):
                The local path to the patched file to review.

            base_command (list of unicode):
                The base command used to run pycodestyle.

            **kwargs (dict, unused):
                Additional keyword arguments.
        """
        output = execute(base_command + [path],
                         split_lines=True,
                         ignore_errors=True)

        for line in output:
            try:
                error_code, line_num, column, message = line.split(':', 3)
                line_num = int(line_num)
                column = int(column)
            except Exception as e:
                self.logger.error('Cannot parse pycodestyle line "%s": %s',
                                  line, e)
                continue

            f.comment(text=message.strip(),
                      first_line=line_num,
                      start_column=column,
                      error_code=error_code)
