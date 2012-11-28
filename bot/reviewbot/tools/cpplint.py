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

import re
import logging

from celery.utils.log import get_task_logger
from reviewbot.tools.process import execute
from reviewbot.tools import Tool

logger = get_task_logger("WORKER")

class cpplintTool(Tool):
    name = 'CPP-Lint Style Checker'
    version = '0.1'
    description = "Checks code for style errors using the Google CPP Lint (Modified by E///) tool."
    options = [
        {
            'name': 'verbosity',
            'field_type': 'django.forms.IntegerField',
            'default': 1,
            'field_options': {
                'label': 'Verbosity level for CPP Lint',
                'help_text': 'Which level of messages should be displayed.  1 = All, 5=Few',
                'required': True,
            },
        },
        {
            'name': 'excluded_checks',
            'field_type': 'django.forms.CharField',
            'default': "",
            'field_options': {
                'label': 'Tests to exclude',
                'help_text': 'Comma seperated list of tests to exclude (run cpplint.py --filter= to see all possible choices)',
                'required': False,
            },
        },
    ]

    def handle_file(self, f):
        logger.info("Filename to parse is: %s" % f.dest_file)
        if not (f.dest_file.endswith('.cpp') or f.dest_file.endswith('.h')):
            # Ignore the file.
            logger.info("File %s is not for us." % f)
            return False

        path = f.get_patched_file_path()
        if not path:
            logger.info("Unable to create tmpfile")
            return False

        # Run the script and capture the output.
        if self.settings['excluded_checks']:
            output = execute(
                [
                    'cpplint.py',
                    '--verbose=%i' % self.settings['verbosity'],
                    '--filter=%s' % self.settings['excluded_checks'],
                    path
                ],
                split_lines=True,
                ignore_errors=True)
        else:
             output = execute(
                [
                    'cpplint.py',
                    '--verbose=%i' % self.settings['verbosity'],
                    path
                ],
                split_lines=True,
                ignore_errors=True)

        # Now for each line extract the fields and add a comment to the file.
        for line in output:
            # Regexp to extract the fields from strings like:
            # filename.cpp:126:  Use int16/int64/etc, rather than the C type long  [runtime/int] [4]
            # filename.cpp:127:  Lines should be <= 132 characters long  [whitespace/line_length] [2]
            # filename.cpp:129:  Use int16/int64/etc, rather than the C type long  [runtime/int] [4]
            matchObj = re.findall(r'(\S+:)(\d+:)(.+?\[)(.+?\])(.+)', line)
            # pre declare all the variables so that they can be used outside the loop if the match (regexp search) worked.
            filename = ""
            linenumber = 0
            freetext = ""
            category = ""
            verbosity = ""
            for tuple in matchObj:
                filename = tuple[0][:-1]  ## filename (: stripped from the end)
                linenumber = int(tuple[1][:-1])  ## linenumber (: stripped from the end)
                freetext = tuple[2][:-1].strip()  ## freetext ( [ stripped from the end)
                category = tuple[3][:-1].strip()  ## category ( ] stripped from the end)
                verbosity = tuple[4][2:-1].strip()  ## verbosity (we just want the number between [])

            # If we found a matchobj then the variables will not be empty and thus we can add a comment to this file object.
            if matchObj:
                f.comment('%s.\n\nError Group: %s\nVerbosity Level: %s' % (freetext, category, verbosity), linenumber)

        return True
