"""Review Bot tool to run JSHint."""

from __future__ import unicode_literals

import json
import os

from reviewbot.config import config
from reviewbot.tools.base import BaseTool, FilePatternsFromSettingMixin
from reviewbot.utils.filesystem import make_tempfile
from reviewbot.utils.process import execute


class JSHintTool(FilePatternsFromSettingMixin, BaseTool):
    """Review Bot tool to run jshint."""

    name = 'JSHint'
    version = '1.0'
    description = (
        'Checks JavaScript code for style errors and potential problems '
        'using JSHint, a JavaScript Code Quality Tool.'
    )
    timeout = 30

    exe_dependencies = ['jshint']

    file_patterns = ['*.js']
    file_extension_setting = ['extra_ext_checks']

    options = [
        {
            'name': 'extra_ext_checks',
            'field_type': 'django.forms.CharField',
            'default': '',
            'field_options': {
                'label': 'Extra file extensions',
                'help_text': (
                    'A comma-separated list of extra file extensions to '
                    'check (only .js is included by default).'
                ),
                'required': False,
            },
        },
        {
            'name': 'extract_js_from_html',
            'field_type': 'django.forms.ChoiceField',
            'field_options': {
                'label': 'Extract JavaScript from HTML',
                'help_text': (
                    'Whether JSHint should extract JavaScript from HTML '
                    'files. If set to "auto", it will only try extracting '
                    'JavaScript if the file looks like an HTML file.'
                ),
                'choices': (
                    ('auto', 'auto'),
                    ('always', 'always'),
                    ('never', 'never'),
                ),
                'initial': 'never',
                'required': False,
            },
        },
        {
            'name': 'config',
            'field_type': 'djblets.db.fields.JSONFormField',
            'default': '',
            'field_options': {
                'label': 'Configuration',
                'help_text': (
                    'JSON specifying which JSHint options to turn on or '
                    'off. (This is equivalent to the contents of a '
                    '.jshintrc file.)'
                ),
                'required': False,
            },
            'widget': {
                'type': 'django.forms.Textarea',
                'attrs': {
                    'cols': 70,
                    'rows': 10,
                },
            },
        },
    ]

    REPORTER_PATH = os.path.abspath(os.path.join(__file__, '..', 'support',
                                                 'js', 'jshint_reporter.js'))

    def build_base_command(self, **kwargs):
        """Build the base command line used to review files.

        If a custom JSHint configuration is set, this will save it to a
        temporary file and pass it along for all JSHint runs.

        Args:
            **kwargs (dict, unused):
                Additional keyword arguments.

        Returns:
            list of unicode:
            The base command line.
        """
        settings = self.settings

        cmd = [
            config['exe_paths']['jshint'],
            '--extract=%s' % settings['extract_js_from_html'],
            '--reporter=%s' % self.REPORTER_PATH,
        ]

        # If any configuration was specified, create a temporary config file.
        # This will be used for each file.
        config_content = self.settings['config']

        if config_content:
            cmd.append('--config=%s'
                       % make_tempfile(content=config_content.encode('utf-8')))

        return cmd

    def handle_file(self, f, path, base_command, **kwargs):
        """Perform a review of a single file.

        Args:
            f (reviewbot.processing.review.File):
                The file to process.

            path (unicode):
                The local path to the patched file to review.

            base_command (list of unicode):
                The base command used to run JSHint.

            **kwargs (dict, unused):
                Additional keyword arguments.
        """
        output = execute(base_command + [path],
                         ignore_errors=True)

        if output:
            errors = json.loads(output)

            for error in errors:
                f.comment(text=error['msg'],
                          first_line=error['line'],
                          start_column=error['column'],
                          error_code=error['code'])
