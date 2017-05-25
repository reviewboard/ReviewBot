from __future__ import unicode_literals

import re

from reviewbot.tools import Tool
from reviewbot.utils.filesystem import make_tempfile
from reviewbot.utils.process import execute, is_exe_in_path


class JSHintTool(Tool):
    """Review Bot tool to run jshint."""

    name = 'JSHint'
    version = '1.0'
    description = ('Checks JavaScript code for style errors and potential '
                   'problems using JSHint, a JavaScript Code Quality Tool.')
    timeout = 30
    options = [
        {
            'name': 'verbose',
            'field_type': 'django.forms.BooleanField',
            'default': False,
            'field_options': {
                'label': 'Verbose',
                'help_text': 'Includes message codes in the JSHint output.',
                'required': False,
            },
        },
        {
            'name': 'extra_ext_checks',
            'field_type': 'django.forms.CharField',
            'default': '',
            'field_options': {
                'label': 'Extra File Extensions',
                'help_text': ('A comma-separated list of extra file '
                              'extensions to check (only .js is included by '
                              'default).'),
                'required': False,
            },
        },
        {
            'name': 'extract_js_from_html',
            'field_type': 'django.forms.ChoiceField',
            'field_options': {
                'label': 'Extract JavaScript from HTML',
                'help_text': ('Whether JSHint should extract JavaScript from '
                              'HTML files. If set to "auto", it will only try '
                              'extracting JavaScript if the file looks like '
                              'an HTML file.'),
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
                'help_text': ('JSON specifying which JSHint options to turn '
                              'on or off. (This is equivalent to the contents '
                              'of a .jshintrc file.)'),
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

    # Each output line looks something like:
    # file.js: line 2, col 14, Use '===' to compare with 'null'.
    REGEX = re.compile(
        r'\S+: line (?P<line_num>\d+), col (?P<col>\d+),(?P<msg>.+)')

    def check_dependencies(self):
        """Verify the tool's dependencies are installed.

        Returns:
            bool:
            True if all dependencies for the tool are satisfied. If this
            returns False, the worker will not listen for this Tool's queue,
            and a warning will be logged.
        """
        return is_exe_in_path('jshint')

    def handle_files(self, files, settings):
        """Perform a review of all files.

        Args:
            files (list of reviewbot.processing.review.File):
                The files to process.

            settings (dict):
                Tool-specific settings.
        """
        # Get any extra file extensions we should process.
        self.file_exts = None

        if settings['extra_ext_checks']:
            self.file_exts = tuple(
                settings['extra_ext_checks'].split(','))

        # If any configuration was specified, create a temporary config file.
        self.config_file = None

        if settings['config']:
            self.config_file = make_tempfile(content=settings['config'])

        super(JSHintTool, self).handle_files(files, settings)

    def handle_file(self, f, settings):
        """Perform a review of a single file.

        Args:
            f (reviewbot.processing.review.File):
                The file to process.

            settings (dict):
                Tool-specific settings.
        """
        # Check if we should process this file, based on its extension.
        if not (f.dest_file.endswith('.js') or
                (self.file_exts and f.dest_file.endswith(self.file_exts))):
            # Ignore the file.
            return

        path = f.get_patched_file_path()

        if not path:
            return

        cmd = ['jshint', '--extract=%s' % settings['extract_js_from_html']]

        if settings['verbose']:
            cmd.append('--verbose')

        if self.config_file:
            cmd.append('--config=%s' % self.config_file)

        cmd.append(path)
        output = execute(cmd, split_lines=True, ignore_errors=True)

        for line in output:
            m = re.match(self.REGEX, line)

            if m:
                f.comment('Col: %s\n%s' % (m.group('col'), m.group('msg')),
                          int(m.group('line_num')))
