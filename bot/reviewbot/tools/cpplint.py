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

import re

from reviewbot.tools import Tool
from reviewbot.tools.process import execute


class CPPLintTool(Tool):
    name = 'CPP-Lint Style Checker'
    version = '0.1'
    description = 'Checks code for style errors using the ' \
                  'Google CPP Lint tool.'
    options = [
        {
            'name': 'verbosity',
            'field_type': 'django.forms.IntegerField',
            'default': 1,
            'min_value': 1,
            'max_value': 5,
            'field_options': {
                'label': 'Verbosity level for CPP Lint',
                'help_text': 'Which level of messages should be displayed.'
                             '1 = All, 5=Few',
                'required': True,
            },
        },
        {
            'name': 'excluded_checks',
            'field_type': 'django.forms.CharField',
            'default': "",
            'field_options': {
                'label': 'Tests to exclude',
                'help_text': 'Comma seperated list of tests to exclude (run '
                             'cpplint.py --filter= to see all possible '
                             'choices).',
                'required': False,
            },
        },
    ]

    def check_dependencies(self):
        return is_exe_in_path('cpplint')

    def handle_file(self, f):
        if not (f.dest_file.lower().endswith('.cpp') or
                f.dest_file.lower().endswith('.h')):
            # Ignore the file.
            return False

        path = f.get_patched_file_path()
        if not path:
            return False

        # Run the script and capture the output.
        if self.settings['excluded_checks']:
            output = execute(
                [
                    'cpplint',
                    '--verbose=%i' % self.settings['verbosity'],
                    '--filter=%s' % self.settings['excluded_checks'],
                    path
                ],
                split_lines=True,
                ignore_errors=True)
        else:

            output = execute(
                [
                    'cpplint',
                    '--verbose=%i' % self.settings['verbosity'],
                    path
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
            filename = ""
            linenumber = 0
            freetext = ""
            category = ""
            verbosity = ""
            for tuple in matching_obj:
                # filename (: stripped from the end)
                filename = tuple[0][:-1]
                # linenumber (: stripped from the end)
                linenumber = int(tuple[1][:-1])
                # freetext ( [ stripped from the end)
                freetext = tuple[2][:-1].strip()
                # category ( ] stripped from the end)
                category = tuple[3][:-1].strip()
                # verbosity (we just want the number between [])
                verbosity = tuple[4][2:-1].strip()

            # If we found a matching_obj then the variables will not be empty
            # and thus we can add a comment to this file object.
            if matching_obj:
                f.comment('%s.\n\nError Group: %s\nVerbosity Level: %s' %
                         (freetext, category, verbosity), linenumber)

        return True
