"""Review Bot tool to run shellcheck."""

from __future__ import unicode_literals

import logging
import re

from reviewbot.tools import Tool
from reviewbot.utils.process import execute, is_exe_in_path


logger = logging.getLogger(__name__)


class ShellCheckTool(Tool):
    """Review Bot tool to run shellcheck."""

    name = 'ShellCheck'
    version = '1.0'
    description = ('Checks bash/sh shell scripts for style and programming '
                   'errors.')
    timeout = 60
    options = [
        {
            'name': 'severity',
            'field_type': 'django.forms.ChoiceField',
            'field_options': {
                'label': 'Minimum Severity',
                'help_text': ('Minimum severity of errors to consider '
                              '(style, info, warning, error).'),
                'choices': (
                    ('style', 'style'),
                    ('info', 'info'),
                    ('warning', 'warning'),
                    ('error', 'error'),
                ),
                'initial': 'style',
                'required': False,
            },
        },
        {
            'name': 'exclude',
            'field_type': 'django.forms.CharField',
            'default': "",
            'field_options': {
                'label': 'Exclude',
                'help_text': ('A comma-separated of specified codes to be '
                              'excluded from the report. This will be passed '
                              'to the --exclude command line argument (e.g. '
                              'SC1009,SC1073).'),
                'required': False,
            },
        },
    ]

    def __init__(self):
        """Initialize the tool."""
        super(ShellCheckTool, self).__init__()
        self.shebang_regex = re.compile(r'''(
            # Using the Bash shell
            (\#!/bin/bash)
            |

            # Using a POSIX-sh compatible shell
            (\#!/bin/sh)
            |

            # Using the env utility
            (\#!/usr/bin/env bash)
            |

            # Using the env utility
            (\#!/usr/bin/env sh)
            )''', re.VERBOSE)

    def check_dependencies(self):
        """Verify that the tool's dependencies are installed.

        Returns:
            bool:
            True if all dependencies for the tool are satisfied. If this
            returns False, the worker will not be listed for this Tool's queue,
            and a warning will be logged.
        """
        return is_exe_in_path('shellcheck')

    def handle_file(self, f, settings):
        """Perform a review of a single file.

        Args:
            f (reviewbot.processing.review.File):
                The file to process.

            settings (dict):
                Tool-specific settings.
        """
        path = f.get_patched_file_path()

        if not path:
            return

        # Ignore the file if it does not have a .sh extension or a shebang
        # with a supported shell.
        if not f.dest_file.lower().endswith('.sh'):
            with open(path) as patched_file:
                first_line = patched_file.readline()

                if not self.shebang_regex.search(first_line):
                    return
        try:
            output = execute(
                [
                    'shellcheck',
                    '--severity=%s' % settings['severity'],
                    '--exclude=%s' % settings['exclude'],
                    '--format=gcc',
                    path,
                ],
                split_lines=True,
                ignore_errors=True)
        except Exception as e:
            logger.exception('ShellCheck failed: %s', e)

        for line in output:
            try:
                # Strip off the filename, since it might have colons in it.
                line = line[len(path) + 1:]
                line_num, column, message = line.split(':', 2)
                f.comment(message.strip(), int(line_num))
            except Exception as e:
                logger.exception('Cannot parse the shellcheck output: %s', e)
