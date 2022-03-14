"""Review Bot tool to run PMD."""

from __future__ import unicode_literals

import json
import os

from reviewbot.config import config
from reviewbot.tools.base import (BaseTool,
                                  FilePatternsFromSettingMixin,
                                  JavaToolMixin)
from reviewbot.utils.filesystem import make_tempfile
from reviewbot.utils.process import execute


class PMDTool(JavaToolMixin, FilePatternsFromSettingMixin, BaseTool):
    """Review Bot tool to run PMD."""

    name = 'PMD'
    version = '1.0'
    description = 'Checks code for errors using the PMD source code checker.'
    timeout = 90

    exe_dependencies = ['java', 'pmd']

    file_extensions_setting = 'file_ext'

    options = [
        {
            'name': 'rulesets',
            'field_type': 'django.forms.CharField',
            'default': '',
            'field_options': {
                'label': 'Rulesets',
                'help_text': (
                    'A comma-separated list of rulesets to apply or a '
                    'ruleset XML configuration, starting with "<?xml"',
                ),
                'required': True,
            },
            'widget': {
                'type': 'django.forms.Textarea',
                'attrs': {
                    'cols': 80,
                    'rows': 10,
                },
            }
        },
        {
            'name': 'file_ext',
            'field_type': 'django.forms.CharField',
            'default': 'java',
            'field_options': {
                'label': 'Scan files',
                'help_text': (
                    'Comma-separated list of file extensions to scan. Leave '
                    'it empty to check all files.'
                ),
                'required': False,
            },
        },
    ]

    def build_base_command(self, **kwargs):
        """Build the base command line used to review files.

        This creates a command line for running PMD that specifies the
        correct output format and the rulesets (generating a temporary
        ruleset configuration file, if needed).

        Args:
            **kwargs (dict, unused):
                Additional keyword arguments.

        Returns:
            list of unicode:
            The base command line.
        """
        rulesets = self.settings['rulesets']

        if rulesets.startswith('<?xml'):
            rulesets = make_tempfile(rulesets.encode('utf-8'))

        return [
            config['exe_paths']['pmd'],
            'pmd',
            '-no-cache',
            '-f', 'json',
            '-R', rulesets,
        ]

    def handle_file(self, f, path, base_command, **kwargs):
        """Perform a review of a single file.

        Args:
            f (reviewbot.processing.review.File):
                The file to process.

            path (unicode):
                The local path to the patched file to review.

            base_command (list of unicode, optional):
                The common base command line used for reviewing a file.

            **kwargs (dict, unused):
                Additional keyword arguments.
        """
        report_file = make_tempfile()

        output, errors = execute(
            base_command + [
                '-d', path,
                '-r', report_file,
            ],
            ignore_errors=True,
            return_errors=True)

        # Load the report. If we fail to load it for any reason (it's empty
        # or missing), we'll be reporting the stderr output.
        try:
            with open(report_file, 'r') as fp:
                report = json.loads(fp.read())
        except Exception:
            report = None

        if not report:
            # Something went wrong, so let's tell the user about it.
            # First, though, filter out the errors and sanitize them.
            rulesets_file = base_command[-1]

            error_output = '\n'.join(
                _error
                .replace(os.path.realpath(path), f.source_file)
                .replace(rulesets_file,
                         '<check ruleset configuration>')
                .replace(report_file,
                         '<generated report>')
                for _error in errors.splitlines()
                if _error.startswith(('ERROR:', 'SEVERE:'))
            )

            f.comment('PMD was unable to process this file:\n'
                      '\n'
                      '```\n'
                      '%s\n'
                      '```'
                      % error_output.strip(),
                      first_line=None)
            return

        # Check for any processing errors found in the report. If we find
        # any, we'll want to provide some information as a comment.
        processing_errors = report.get('processingErrors')

        if processing_errors:
            norm_path = os.path.realpath(path)

            for error_info in processing_errors:
                # We'll show the general error message, but not the detailed
                # error message (which is likely to contain a long stack
                # trace with minimal useful information).
                #
                # Sanitize the path, so we're not showing temp files in the
                # error.
                error = (
                    error_info['message']
                    .replace(norm_path, f.source_file)
                    .strip()
                )

                f.comment('PMD was unable to process this file:\n'
                          '\n'
                          '```\n'
                          '%s\n'
                          '```\n'
                          '\n'
                          'Check the file locally for more information.'
                          % error,
                          first_line=None)

            return

        # Make sure there's only a single file. If not, something went wrong,
        # but there isn't really anything the user can do about it. The
        # administrator will need to look into it.
        files = report.get('files', [])

        if len(files) != 1:
            self.logger.error('Expected 1 file in PMD output. Got %s: %r',
                              len(files), files)
            return

        # Report all errors found by PMD.
        for violation in files[0].get('violations', []):
            try:
                description = violation['description']
                first_line = violation['beginline']
                num_lines = violation['endline'] - first_line + 1
                start_column = violation['begincolumn']
            except Exception as e:
                self.logger.error('Error parsing PMD violations: %s: %r',
                                  e, violation)
                continue

            f.comment(text=description,
                      first_line=first_line,
                      num_lines=num_lines,
                      start_column=start_column)
