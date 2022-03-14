# Copyright (c) 2012 Ericsson Television Ltd
# Author D Laird
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
"""Review Bot tool to run Cppcheck."""

from __future__ import unicode_literals

import re

from reviewbot.config import config
from reviewbot.tools.base import BaseTool
from reviewbot.utils.process import execute


class CPPCheckTool(BaseTool):
    """Review Bot tool to run cppcheck."""

    name = 'Cppcheck'
    version = '1.0'
    description = (
        'Checks code for errors using Cppcheck, a tool for static C/C++ '
        'code analysis.'
    )
    timeout = 30

    exe_dependencies = ['cppcheck']
    file_patterns = [
        '*.c', '*.cc', '*.cpp', '.cxx', '*.c++',
        '*.h', '*.hh', '*.hpp', '*.hxx', '*.h++',
        '*.tpp', '*.txx',
    ]

    options = [
        {
            'name': 'style_checks_enabled',
            'field_type': 'django.forms.BooleanField',
            'default': True,
            'field_options': {
                'label': 'Enable standard style checks',
                'help_text': (
                    'Enable the standard style checks, including most '
                    'warning, style, and performance checks.'
                ),
                'required': False,
            },
        },
        {
            'name': 'all_checks_enabled',
            'field_type': 'django.forms.BooleanField',
            'default': False,
            'field_options': {
                'label': 'Enable all error checks',
                'help_text': (
                    'Enable all the error checks. This is likely to include '
                    'many false positives.'
                ),
                'required': False,
            },
        },
        {
            'name': 'force_language',
            'field_type': 'django.forms.ChoiceField',
            'field_options': {
                'label': 'Use language',
                'help_text': 'Force cppcheck to use a specific language.',
                'choices': (
                    ('', 'auto-detect'),
                    ('c', 'C'),
                    ('c++', 'C++'),
                ),
                'initial': '',
                'required': False,
            },
        },
    ]

    ERROR_RE = re.compile(
        r'^(?P<linenum>\d*)::(?P<column>\d+)::(?P<severity>[^:]+)::'
        r'(?P<error_code>[^:]+)::\s*(?P<text>.+)\s*$',
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
        cmdline = [
            config['exe_paths']['cppcheck'],
            '-q',
            '--template={line}::{column}::{severity}::{id}::{message}',
        ]

        # Figure out which checks should be enabled.
        enabled_checks = []

        if settings.get('all_checks_enabled'):
            enabled_checks.append('all')
        elif settings.get('style_checks_enabled'):
            enabled_checks.append('style')

        if enabled_checks:
            cmdline.append('--enable=%s' % ','.join(enabled_checks))

        # Force a specific C variant, if requested.
        force_language = settings.get('force_language')

        if force_language:
            cmdline.append('--language=%s' % force_language)

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
            try:
                column = int(m.group('column'))
            except ValueError:
                column = None

            f.comment(text=m.group('text'),
                      first_line=int(m.group('linenum') or 0),
                      start_column=column,
                      severity=m.group('severity'),
                      error_code=m.group('error_code'))
