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
"""Review Bot tool to run cpplint."""

from __future__ import unicode_literals

import re

from reviewbot.config import config
from reviewbot.tools.base import BaseTool
from reviewbot.utils.process import execute


class CPPLintTool(BaseTool):
    """Review Bot tool to run cpplint."""

    name = 'cpplint'
    version = '1.0'
    description = "Checks code for style errors using Google's cpplint tool."
    timeout = 30

    exe_dependencies = ['cpplint']
    file_patterns = [
        '*.c', '*.cc', '*.cpp', '.cxx', '*.c++', '*.cu',
        '*.h', '*.hh', '*.hpp', '*.hxx', '*.h++', '*.cuh',
    ]

    options = [
        {
            'name': 'verbosity',
            'field_type': 'django.forms.IntegerField',
            'default': 1,
            'min_value': 1,
            'max_value': 5,
            'field_options': {
                'label': 'Verbosity level for cpplint',
                'help_text': (
                    'Which level of messages should be displayed. '
                    '1=All, 5=Few.'
                ),
                'required': True,
            },
        },
        {
            'name': 'excluded_checks',
            'field_type': 'django.forms.CharField',
            'default': '',
            'field_options': {
                'label': 'Tests to exclude',
                'help_text': (
                    'Comma-separated list of tests to exclude (run cpplint '
                    '--filter= to see all possible choices).'
                ),
                'required': False,
            },
        },
    ]

    ERROR_RE = re.compile(
        r'^[^:]+:(?P<linenum>\d+):\s+(?P<text>.*?)\s+'
        r'\[(?P<category>[^\]]+)\] \[[0-5]\]$',
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
        verbosity = settings['verbosity']
        excluded_checks = settings.get('excluded_checks')

        cmdline = [
            config['exe_paths']['cpplint'],
            '--verbose=%s' % verbosity,
        ]

        if excluded_checks:
            cmdline.append('--filter=%s' % excluded_checks)

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
            # Note that some errors may have a line number of 0 (indicating
            # that a copyright header isn't present). We'll be converting this
            # to 1.
            f.comment(text=m.group('text'),
                      first_line=int(m.group('linenum')) or 1,
                      error_code=m.group('category'))
