"""Review Bot tool to run checkstyle."""

from __future__ import unicode_literals

import logging
from xml.etree import ElementTree

from reviewbot.config import config
from reviewbot.tools import Tool
from reviewbot.utils.filesystem import make_tempfile
from reviewbot.utils.process import execute, is_exe_in_path


class CheckstyleTool(Tool):
    """Review Bot tool to run checkstyle."""

    name = 'checkstyle'
    version = '1.0'
    description = 'Checks code for errors using checkstyle.'
    timeout = 90
    options = [
        {
            'name': 'config',
            'field_type': 'django.forms.CharField',
            'default': '',
            'field_options': {
                'label': 'Configuration xml',
                'help_text': 'Content of configuration xml. See: '
                             'http://checkstyle.sourceforge.net/config.html',
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
    ]

    def check_dependencies(self):
        """Verify the tool's dependencies are installed.

        Returns:
            bool:
            True if all dependencies for the tool are satisfied. If this
            returns False, the worker will not listen for this Tool's queue,
            and a warning will be logged.
        """
        checkstyle_path = config['checkstyle_path']
        return (checkstyle_path and is_exe_in_path(checkstyle_path) and
                is_exe_in_path('java'))

    def handle_file(self, f, settings):
        """Perform a review of a single file.

        Args:
            f (reviewbot.processing.review.File):
                The file to process.

            settings (dict):
                Tool-specific settings.
        """
        if not f.dest_file.lower().endswith('.java'):
            # Ignore the file.
            return

        path = f.get_patched_file_path()

        if not path:
            return

        cfgXml = make_tempfile(settings['config'])
        outfile = make_tempfile()

        execute(
            [
                'java',
                '-jar',
                config['checkstyle_path'],
                '-c', cfgXml,
                '-f', 'xml',
                '-o', outfile,
                path,
            ],
            ignore_errors=True)

        try:
            root = ElementTree.parse(outfile).getroot()
            for row in root.iter('error'):
                f.comment(row.get('message'), int(row.get('line')))
        except Exception as e:
            logging.error('Cannot parse xml file: %s', e)
