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

from __future__ import unicode_literals

import re

from reviewbot.tools import Tool
from reviewbot.utils.process import execute, is_exe_in_path


class CPPLintTool(Tool):
    """Review Bot tool to run cpplint."""

    name = 'cpplint'
    version = '1.0'
    description = ("Checks code for style errors using Google's cpplint "
                   "tool.")
    timeout = 30
    options = [
        {
            'name': 'verbosity',
            'field_type': 'django.forms.IntegerField',
            'default': 1,
            'min_value': 1,
            'max_value': 5,
            'field_options': {
                'label': 'Verbosity level for CPP Lint',
                'help_text': ('Which level of messages should be displayed. '
                              '1=All, 5=Few.'),
                'required': True,
            },
        },
        {
            'name': 'excluded_checks',
            'field_type': 'django.forms.CharField',
            'default': "",
            'field_options': {
                'label': 'Tests to exclude',
                'help_text': ('Comma-separated list of tests to exclude (run '
                              'cpplint.py --filter= to see all possible '
                              'choices).'),
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
        return is_exe_in_path('cpplint')

    def handle_file(self, f, settings):
        """Perform a review of a single file.

        Args:
            f (reviewbot.processing.review.File):
                The file to process.

            settings (dict):
                Tool-specific settings.
        """
        if not (f.dest_file.lower().endswith('.cpp') or
                f.dest_file.lower().endswith('.h')):
            # Ignore the file.
            return

        path = f.get_patched_file_path()

        if not path:
            return

        # Run the script and capture the output.
        if settings['excluded_checks']:
            output = execute(
                [
                    'cpplint',
                    '--verbose=%s' % settings['verbosity'],
                    '--filter=%s' % settings['excluded_checks'],
                    path,
                ],
                split_lines=True,
                ignore_errors=True)
        else:
            output = execute(
                [
                    'cpplint',
                    '--verbose=%s' % self.settings['verbosity'],
                    path,
                ],
                split_lines=True,
                ignore_errors=True)

        # Now for each line extract the fields and add a comment to the file.
        for line in output:
            # Regexp to extract the fields from strings like:
            # filename.cpp:126: \
            #   Use int16/int64/etc, rather than the C type long \
            #   [runtime/int] [4]
            # filename.cpp:127: \
            #   Lines should be <= 132 characters long \
            #   [whitespace/line_length] [2]
            # filename.cpp:129: \
            #   Use int16/int64/etc, rather than the C type long \
            #   [runtime/int] [4]
            matching_obj = re.findall(r'(\S+:)(\d+:)(.+?\[)(.+?\])(.+)', line)
            # pre declare all the variables so that they can be used outside
            # the loop if the match (regexp search) worked.
            linenumber = 0
            freetext = ''
            category = ''
            verbosity = ''

            for match in matching_obj:
                # linenumber (: stripped from the end)
                linenumber = int(match[1][:-1])
                # freetext ( [ stripped from the end)
                freetext = match[2][:-1].strip()
                # category ( ] stripped from the end)
                category = match[3][:-1].strip()
                # verbosity (we just want the number between [])
                verbosity = match[4][2:-1].strip()

                f.comment('%s.\n\nError Group: %s\nVerbosity Level: %s' %
                          (freetext, category, verbosity), linenumber)
