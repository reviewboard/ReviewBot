"""Review Bot tool to run flake8."""

from __future__ import unicode_literals

import json

import six

from reviewbot.config import config
from reviewbot.tools.base import BaseTool
from reviewbot.tools.utils.codeclimate import \
    add_comment_from_codeclimate_issue
from reviewbot.utils.process import execute


class Flake8Tool(BaseTool):
    """Review Bot tool to run flake8."""

    name = 'flake8'
    version = '1.0'
    description = 'Checks Python code for style and programming errors.'
    timeout = 30

    exe_dependencies = ['flake8']
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
            'default': "",
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
        ignore = settings.get('ignore')

        cmdline = [
            config['exe_paths']['flake8'],
            '--exit-zero',
            '--format=codeclimate',
            '--max-line-length=%s' % settings['max_line_length'],
        ]

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
                The base command used to run flake8.

            **kwargs (dict, unused):
                Additional keyword arguments.
        """
        output = execute(base_command + [path])

        try:
            payload = json.loads(output)
        except Exception as e:
            self.logger.error('Unable to parse JSON data from flake8: %s: %r',
                              e, output)
            return

        assert len(payload) == 1
        issues = next(six.itervalues(payload))

        for issue in issues:
            add_comment_from_codeclimate_issue(issue_payload=issue,
                                               review_file=f)
