"""Review Bot tool to run checkstyle."""

from __future__ import unicode_literals

import logging
from xml.etree import ElementTree

from reviewbot.config import config
from reviewbot.tools.base import BaseTool, JavaToolMixin
from reviewbot.utils.filesystem import make_tempfile
from reviewbot.utils.process import execute


class CheckstyleTool(JavaToolMixin, BaseTool):
    """Review Bot tool to run checkstyle."""

    name = 'checkstyle'
    version = '1.0'
    description = 'Checks code for errors using checkstyle.'
    timeout = 90

    file_patterns = ['*.java']
    java_main = 'com.puppycrawl.tools.checkstyle.Main'
    java_classpaths_key = 'checkstyle'

    options = [
        {
            'name': 'config',
            'field_type': 'django.forms.CharField',
            'default': '',
            'field_options': {
                'label': 'Configuration XML',
                'help_text': (
                    'This can be the name of a Checkstyle-provided XML '
                    'configuration ("google_checks.xml" or "sun_checks.xml"), '
                    'or the contents of a custom configuration XML file (see '
                    'https://checkstyle.sourceforge.io/config.html).'
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
        config_xml = self.settings['config'].strip()

        if config_xml.startswith('<?xml'):
            config_xml = make_tempfile(config_xml.encode('utf-8'),
                                       extension='.xml')

        return super(CheckstyleTool, self).build_base_command(**kwargs) + [
            '-f=xml',
            '-c=%s' % config_xml,
        ]

    def handle_file(self, f, path, base_command, **kwargs):
        """Perform a review of a single file.

        Args:
            f (reviewbot.processing.review.File):
                The file to process.

            path (unicode):
                The local path to the patched file to review.

            base_command (list of unicode):
                The base command used to run checkstyle.

            **kwargs (dict, unused):
                Additional keyword arguments.
        """
        output = execute(base_command + [path],
                         with_errors=False,
                         ignore_errors=True)

        try:
            root = ElementTree.fromstring(output)
        except Exception:
            f.comment(text=("checkstyle wasn't able to parse this file. Check "
                            "the file for syntax errors, and make sure that "
                            "your configured settings in Review Bot are "
                            "correct."),
                      first_line=None)

            return

        for error in root.iter('error'):
            column = error.get('column')

            if column:
                column = int(column)

            f.comment(text=error.get('message'),
                      first_line=int(error.get('line')),
                      start_column=column,
                      severity=error.get('severity'),
                      error_code=error.get('source'))
