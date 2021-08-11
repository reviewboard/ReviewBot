"""Review Bot tool to run pydocstyle."""

from __future__ import unicode_literals

import re

from reviewbot.config import config
from reviewbot.tools.base import BaseTool
from reviewbot.utils.process import execute


class PydocstyleTool(BaseTool):
    """Review Bot tool to run pydocstyle."""

    name = 'pydocstyle'
    version = '1.0'
    description = 'Checks Python code for docstring conventions.'
    timeout = 30

    exe_dependencies = ['pydocstyle']
    file_patterns = ['*.py']

    options = [
        {
            'name': 'ignore',
            'field_type': 'django.forms.CharField',
            'default': '',
            'field_options': {
                'label': 'Ignore',
                'help_text': (
                    'A comma-separated list of errors or prefixes to ignore. '
                    'For example, passing D1 will ignore all error codes '
                    'beginning with "D1" (i.e. D1, D10). The list will be '
                    'passed to the --ignore command line argument. If no '
                    'arguments are specified, pydocstyle will default to '
                    'PEP 257 convention.'
                ),
                'required': False,
            },
        },
    ]

    ERROR_RE = re.compile(
        r'^(?P<filename>.*):(?P<linenum>\d+) .*:\n'
        r'\s+(?P<error_code>D\d{3}): (?P<text>.*)\s*$',
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
        settings = self.settings
        ignore = settings.get('ignore')

        cmdline = [config['exe_paths']['pydocstyle']]

        if ignore:
            cmdline.append('--ignore=%s' % ignore)

        return cmdline

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
                         ignore_errors=True)

        for m in self.ERROR_RE.finditer(output):
            f.comment(text=m.group('text'),
                      first_line=int(m.group('linenum')),
                      error_code=m.group('error_code'))
