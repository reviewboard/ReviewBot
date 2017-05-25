from __future__ import unicode_literals

import csv

from reviewbot.config import config
from reviewbot.tools import Tool
from reviewbot.utils.process import execute, is_exe_in_path


class PMDTool(Tool):
    """Review Bot tool to run PMD."""

    name = 'PMD'
    version = '1.0'
    description = 'Checks code for errors using the PMD source code checker.'
    timeout = 30
    options = [
        {
            'name': 'rulesets',
            'field_type': 'django.forms.CharField',
            'default': '',
            'field_options': {
                'label': 'Rulesets',
                'help_text': 'A comma-separated list of rulesets to apply.',
                'required': True,
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
        path = f.get_patched_file_path()

        if not path:
            return

        output = execute(
            [
                config['pmd_path'],
                'pmd',
                '-d', path,
                '-R', settings['rulesets'],
                '-f', 'csv',
            ],
            split_lines=True,
            ignore_errors=True)

        reader = csv.DictReader(output)

        for row in reader:
            f.comment(row['Description'], int(row['Line']))
