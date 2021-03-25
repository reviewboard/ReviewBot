from __future__ import unicode_literals

import csv
import logging

from reviewbot.config import config
from reviewbot.tools.base import BaseTool, FilePatternsFromSettingMixin
from reviewbot.utils.filesystem import make_tempfile
from reviewbot.utils.process import execute


class PMDTool(FilePatternsFromSettingMixin, BaseTool):
    """Review Bot tool to run PMD."""

    name = 'PMD'
    version = '1.0'
    description = 'Checks code for errors using the PMD source code checker.'
    timeout = 90

    exe_dependencies = ['pmd']

    file_extensions_setting = 'file_ext'

    options = [
        {
            'name': 'rulesets',
            'field_type': 'django.forms.CharField',
            'default': '',
            'field_options': {
                'label': 'Rulesets',
                'help_text': 'A comma-separated list of rulesets to apply or '
                             'a ruleset XML configuration, starting with '
                             '"<?xml"',
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
                'help_text': 'Comma-separated list of file extensions '
                             'to scan. Leave it empty to check all files.',
                'required': False,
            },
        },
    ]

    def handle_file(self, f, **kwargs):
        """Perform a review of a single file.

        Args:
            f (reviewbot.processing.review.File):
                The file to process.

            settings (dict):
                Tool-specific settings.
        """
        path = f.get_patched_file_path()

        if not path:
            return

        rulesets = self.settings['rulesets']

        if rulesets.startswith('<?xml'):
            rulesets = make_tempfile(rulesets.encode('utf-8'))

        outfile = make_tempfile()

        # TODO: We should move to using json in the future, if there aren't
        #       any compatibility problems.
        execute(
            [
                config['exe_paths']['pmd'],
                'pmd',
                '-d', path,
                '-R', rulesets,
                '-f', 'csv',
                '-r', outfile,
            ],
            ignore_errors=True)

        with open(outfile, 'r') as result:
            reader = csv.DictReader(result)

            for row in reader:
                try:
                    f.comment(row['Description'], int(row['Line']))
                except Exception as e:
                    logging.error('Cannot parse line "%s": %s', row, e)
