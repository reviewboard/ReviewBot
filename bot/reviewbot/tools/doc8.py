"""Review Bot tool to run doc8."""

from __future__ import unicode_literals

import re

from celery.utils.log import get_task_logger

from reviewbot.config import config
from reviewbot.tools.base import BaseTool
from reviewbot.utils.process import execute


logger = get_task_logger(__name__)


class Doc8Tool(BaseTool):
    """Review Bot tool to run doc8."""

    name = 'doc8'
    version = '1.0'
    description = 'Checks reStructuredText for style.'
    timeout = 30

    exe_dependencies = ['doc8']
    file_patterns = ['*.rst']

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

    LINE_RE = re.compile(
        r'^.+:(?P<linenum>\d+): (?P<error_code>D\d{3}) (?P<text>.+)')

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

        return [
            config['exe_paths']['doc8'],
            '-q',
            '--max-line-length=%s' % settings['max_line_length'],
            '--file-encoding=%s' % settings['encoding'],
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
        output = execute(base_command + [path],
                         split_lines=True,
                         ignore_errors=True)

        line_re = self.LINE_RE

        for line in output:
            m = line_re.match(line)

            if m:
                # We've validated the types in the regex above, so we should
                # be safe to cast to int here.
                f.comment(text=m.group('text'),
                          first_line=int(m.group('linenum')),
                          error_code=m.group('error_code'))
