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

import logging

from celery.utils.log import get_task_logger
from reviewbot.tools.process import execute
from reviewbot.tools import Tool

logger = get_task_logger("WORKER")

class cppcheckTool(Tool):
    name = 'CPPCheck - Static Code Analaysis'
    version = '0.1'
    description = "Checks code for errors, and potential errors using the Open Source CPPcheck."
    options = [
        {
            'name': 'style_checks_enabled',
            'field_type': 'django.forms.BooleanField',
            'default': True,
            'field_options': {
                'label': 'Enable standard style checks',
                'help_text': 'This will enable the standard style checks - this also enables most warning, style and performance checks',
                'required': False,
            },
        },
        {
            'name': 'all_checks_enabled',
            'field_type': 'django.forms.BooleanField',
            'default': False,
            'field_options': {
                'label': 'Enable ALL error checks',
                'help_text': 'This will enable ALL the error checks - likely to have many false postives.',
                'required': False,
            },
        },
    ]

    def handle_file(self, f):
        logger.info("Filename to parse is: %s" % f.dest_file)
        if not (f.dest_file.endswith('.cpp') or f.dest_file.endswith('.h') or f.dest_file.endswith('.c')):
            # Ignore the file.
            logger.info("File %s is not for us." % f)
            return False

        path = f.get_patched_file_path()
        if not path:
            logger.info("Unable to create tmpfile")
            return False

        enabled_checks = []

        # Check the options we want to pass to cppcheck.
        if self.settings['style_checks_enabled']:
            enabled_checks.append('style')

        if self.settings['all_checks_enabled']:
            enabled_checks.append('all')

        # Create string to pass to cppcheck
        enable_settings = '%s' % ','.join(map(str, enabled_checks))
        logger.info("Cppcheck options will be: %s" % enable_settings)

        # Run the script and capture the output.
        output = execute(
            [
                'cppcheck',
                '--template=\"{file}::{line}::{severity}::{id}::{message}\"',
                '--enable=%s' % enable_settings,
                path
            ],
            split_lines=True,
            ignore_errors=True)
        

        # Now for each line extract the fields and add a comment to the file.
        for line in output:
            # filename.cpp,849,style,unusedFunction,The function 'bob' is never used
            # filename.cpp,638,style,unusedFunction,The function 'peter' is never used
            # filename.cpp,722,style,unusedFunction,The function 'test' is never used
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
                freetext = parsed[4][:-1] ## strip the " from the end

                # logger.info("%s.\n\nCategory: %s\nSub Category: %s" % (freetext, category, sub_category))
                # If the message is that its an error then open as Issue else just add comment.
                if category == 'error':
                    f.comment('%s.\n\nCategory: %s\nSub Category: %s' % (freetext, category, sub_category), linenumber, issue=True)
                else:
                    f.comment('%s.\n\nCategory: %s\nSub Category: %s' % (freetext, category, sub_category), linenumber)

        return True
