# Copyright (c) 2012 Ericsson Television Ltd
# Author D Laird
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#  * Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation and/or
# other materials provided with the distribution.
#  * All advertising materials mentioning features or use of this software must
# display the following acknowledgement: This product includes software developed
# by %ORGANIZATION% and its contributors.
#  * Neither the name of %ORGANIZATION% nor the names of its contributors may be
# used to endorse or promote products derived from this software without specific
# prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

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
