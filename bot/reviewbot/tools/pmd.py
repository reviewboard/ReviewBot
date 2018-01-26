from __future__ import unicode_literals

import csv
import logging
from os.path import splitext

from reviewbot.config import config
from reviewbot.tools import Tool
from reviewbot.utils.filesystem import make_tempfile
from reviewbot.utils.process import execute, is_exe_in_path


class PMDTool(Tool):
    """Review Bot tool to run PMD."""

    name = 'PMD'
    version = '1.0'
    description = 'Checks code for errors using the PMD source code checker.'
    timeout = 90
    options = [
        {
            'name': 'rulesets',
            'field_type': 'django.forms.CharField',
            'default': '',
            'field_options': {
                'label': 'Rulesets',
                'help_text': 'A comma-separated list of rulesets to apply or '
                             'an XML configuration starting with "<?xml"',
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
                             'to scan. Leave it empty to check any file.',
                'required': False,
            },
        },
    ]

    def check_dependencies(self):
        """Verify the tool's dependencies are installed.

        Returns:
            bool:
            True if all dependencies for the tool are satisfied. If this
            returns False, the worker will not listen for this Tool's queue,
            and a warning will be logged.
        """
        pmd_path = config['pmd_path']
        return pmd_path and is_exe_in_path(pmd_path)

    def handle_file(self, f, settings):
        """Perform a review of a single file.

        Args:
            f (reviewbot.processing.review.File):
                The file to process.

            settings (dict):
                Tool-specific settings.
        """
        file_ext = settings['file_ext'].strip()

        if file_ext:
            ext = splitext(f.dest_file)[1][1:]

            if not ext.lower() in file_ext.split(','):
                # Ignore the file.
                return

        path = f.get_patched_file_path()

        if not path:
            return

        rulesets = settings['rulesets']

        if rulesets.startswith('<?xml'):
            rulesets = make_tempfile(rulesets)

        outfile = make_tempfile()

        execute(
            [
                config['pmd_path'],
                'pmd',
                '-d', path,
                '-R', rulesets,
                '-f', 'csv',
                '-r', outfile
            ],
            ignore_errors=True)

        with open(outfile) as result:
            reader = csv.DictReader(result)

            for row in reader:
                try:
                    f.comment(row['Description'], int(row['Line']))
                except Exception as e:
                    logging.error('Cannot parse line "%s": %s', row, e)
