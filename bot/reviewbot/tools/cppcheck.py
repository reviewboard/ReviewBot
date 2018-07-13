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

from reviewbot.tools import Tool
from reviewbot.utils.process import execute, is_exe_in_path


class CPPCheckTool(Tool):
    """Review Bot tool to run cppcheck."""

    name = 'Cppcheck'
    version = '1.0'
    description = ('Checks code for errors using Cppcheck, a tool for static '
                   'C/C++ code analysis.')
    timeout = 30
    options = [
        {
            'name': 'style_checks_enabled',
            'field_type': 'django.forms.BooleanField',
            'default': True,
            'field_options': {
                'label': 'Enable standard style checks',
                'help_text': ('Enable the standard style checks, including '
                              'most warning, style, and performance checks.'),
                'required': False,
            },
        },
        {
            'name': 'all_checks_enabled',
            'field_type': 'django.forms.BooleanField',
            'default': False,
            'field_options': {
                'label': 'Enable ALL error checks',
                'help_text': ('Enable all the error checks. This is likely '
                              'to include many false positives.'),
                'required': False,
            },
        },
        {
            'name': 'force_language',
            'field_type': 'django.forms.ChoiceField',
            'field_options': {
                'label': 'Use language',
                'help_text': ('Force cppcheck to use a specific language.'),
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

    def check_dependencies(self):
        """Verify the tool's dependencies are installed.

        Returns:
            bool:
            True if all dependencies for the tool are satisfied. If this
            returns False, the worker will not listen for this Tool's queue,
            and a warning will be logged.
        """
        return is_exe_in_path('cppcheck')

    def handle_file(self, f, settings):
        """Perform a review of a single file.

        Args:
            f (reviewbot.processing.review.File):
                The file to process.

            settings (dict):
                Tool-specific settings.
        """
        if not (f.dest_file.lower().endswith('.cpp') or
                f.dest_file.lower().endswith('.h') or
                f.dest_file.lower().endswith('.c')):
            # Ignore the file.
            return

        path = f.get_patched_file_path()
        if not path:
            return

        enabled_checks = []

        # Check the options we want to pass to cppcheck.
        if settings['style_checks_enabled']:
            enabled_checks.append('style')

        if settings['all_checks_enabled']:
            enabled_checks.append('all')

        # Create string to pass to cppcheck
        enable_settings = '%s' % ','.join(map(str, enabled_checks))

        cppcheck_args = [
            'cppcheck',
            '--template=\"{file}::{line}::{severity}::{id}::{message}\"',
            '--enable=%s' % enable_settings,
        ]

        lang = settings['force_language'].strip()

        if lang:
            cppcheck_args.append('--language=%s' % lang)

        cppcheck_args.append(path)

        # Run the script and capture the output.
        output = execute(cppcheck_args, split_lines=True, ingore_errors=True)

        # Now for each line extract the fields and add a comment to the file.
        for line in output:
            # filename.cpp,849,style,unusedFunction, \
            #   The function 'bob' is never used
            # filename.cpp,638,style,unusedFunction, \
            #   The function 'peter' is never used
            # filename.cpp,722,style,unusedFunction,
            #   The function 'test' is never used
            parsed = line.split('::')

            # If we have a useful message
            if len(parsed) == 5:
                # Sometimes we dont gets a linenumber (just and empty string)
                # Catch this case and set line number to 0.
                if parsed[1]:
                    linenumber = int(parsed[1])
                else:
                    linenumber = 0

                # Now extract the other options.
                category = parsed[2]
                sub_category = parsed[3]
                freetext = parsed[4][:-1]  # strip the " from the end

                # If the message is that its an error then override the
                # default settings and raise an Issue otherwise just
                # add a comment.
                if category == 'error':
                    f.comment('%s.\n\nCategory: %s\nSub Category: %s' %
                              (freetext, category, sub_category),
                              linenumber, issue=True)
                else:
                    f.comment('%s.\n\nCategory: %s\nSub Category: %s' %
                              (freetext, category, sub_category),
                              linenumber, issue=False)
