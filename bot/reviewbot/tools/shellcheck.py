"""Review Bot tool to run shellcheck."""

from __future__ import unicode_literals

import json
import re

from reviewbot.config import config
from reviewbot.tools.base import BaseTool
from reviewbot.utils.process import execute
from reviewbot.utils.text import split_comma_separated


class ShellCheckTool(BaseTool):
    """Review Bot tool to run shellcheck."""

    name = 'ShellCheck'
    version = '1.0'
    description = (
        'Checks bash/sh shell scripts for style and programming errors.'
    )
    timeout = 60

    exe_dependencies = ['shellcheck']
    file_patterns = ['*.bash', '*.bats', '*.dash', '*.ksh', '*.sh']

    options = [
        {
            'name': 'severity',
            'field_type': 'django.forms.ChoiceField',
            'field_options': {
                'label': 'Minimum severity',
                'help_text': (
                    'Minimum severity of errors to consider (style, info, '
                    'warning, error).'
                ),
                'choices': (
                    ('style', 'style'),
                    ('info', 'info'),
                    ('warning', 'warning'),
                    ('error', 'error'),
                ),
                'initial': 'style',
                'required': True,
            },
        },
        {
            'name': 'exclude',
            'field_type': 'django.forms.CharField',
            'default': '',
            'field_options': {
                'label': 'Exclude',
                'help_text': (
                    'A comma-separated of specified codes to be excluded '
                    'from the report. This will be passed to the --exclude '
                    'command line argument (e.g. SC1009,SC1073).'
                ),
                'required': False,
            },
        },
    ]

    SHELL_RE = re.compile(
        br'^#!(/bin/|/usr/bin/|/usr/local/bin/|/usr/bin/env )'
        br'(bash|dash|ksh|sh)')

    def get_can_handle_file(self, review_file, **kwargs):
        """Return whether this tool can handle a given file.

        Args:
            review_file (reviewbot.processing.review.File):
                The file to check.

            **kwargs (dict, unused):
                Additional keyword arguments passed to :py:meth:`execute`.
                This is intended for future expansion.

        Returns:
            bool:
            ``True`` if the file can be handled. ``False`` if it cannot.
        """
        return (
            super(ShellCheckTool, self).get_can_handle_file(review_file,
                                                            **kwargs) or
            self.SHELL_RE.match(review_file.patched_file_contents)
        )

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
        exclude = settings.get('exclude')

        cmdline = [
            config['exe_paths']['shellcheck'],
            '--color=never',
            '--format=json1',
            '--severity=%s' % settings['severity'],
        ]

        if exclude:
            # Normalize the error list, preventing errors if there are spaces
            # or redundant commas.
            cmdline.append('--exclude=%s'
                           % ','.join(split_comma_separated(exclude)))

        return cmdline

    def handle_file(self, f, path, base_command, **kwargs):
        """Perform a review of a single file.

        Args:
            f (reviewbot.processing.review.File):
                The file to process.

            path (unicode):
                The local path to the patched file to review.

            base_command (list of unicode):
                The base command used to run shellcheck.

            **kwargs (dict, unused):
                Additional keyword arguments.
        """
        output = execute(base_command + [path],
                         ignore_errors=True)

        try:
            results = json.loads(output)
        except ValueError:
            self.logger.error(
                'The shellcheck returned an unexpected result. Check to '
                'make sure that your configured settings in the integration '
                'for Review Bot are correct. Shellcheck returned: %s',
                output)

            f.comment(
                text=('The shellcheck returned an unexpected result. Check '
                      'to make sure that your configured settings in Review '
                      'Bot are correct.\n'
                      '\n'
                      'Error message:\n'
                      '```%s```'
                      % output.strip()),
                first_line=None,
                rich_text=True)

            return

        for comment in results.get('comments', []):
            comment_text = comment['message']
            first_line = comment['line']
            num_lines = comment.get('endLine', first_line) - first_line + 1

            fix = comment.get('fix') or {}
            replacements = fix.get('replacements', [])
            replacement_lines = []

            if replacements:
                replacement_lines = f.get_lines(first_line, num_lines)

                # Iterate through all replacements in reverse order of
                # precedence, and build new strings.
                #
                # Each replacement should only span one line. If we see
                # more, log and scrap any replacement lines.
                for replacement in sorted(replacements,
                                          key=lambda r: (r['precedence'],
                                                         r['column']),
                                          reverse=True):
                    replacement_linenum = replacement['line']

                    if replacement['endLine'] != replacement_linenum:
                        self.logger.warning(
                            'Saw multi-line replacement information from '
                            'ShellCheck, which was not possible when this '
                            'tool was developed. Please report this along '
                            'with the file that triggered it (%s) and the '
                            'comment payload information: %r',
                            comment['file'],
                            comment)
                        replacement_lines = []
                        break

                    replacement_insertion_point = replacement['insertionPoint']

                    if replacement_insertion_point not in ('beforeStart',
                                                           'afterEnd'):
                        self.logger.warning(
                            'Saw the replacement point "%s" from ShellCheck, '
                            'which was not available when this tool was '
                            'developed. Please report this along with the '
                            'file that triggered it (%s) and the comment '
                            'payload information: %r',
                            replacement_insertion_point,
                            comment['file'],
                            comment)
                        replacement_lines = []
                        break

                    replacement_norm_linenum = replacement_linenum - first_line

                    replacement_start_column = replacement['column']
                    replacement_end_column = replacement['endColumn']
                    replacement_text = replacement['replacement']
                    replacement_line = \
                        replacement_lines[replacement_norm_linenum]

                    replacement_lines[replacement_norm_linenum] = (
                        b'%s%s%s'
                        % (replacement_line[:replacement_start_column - 1],
                           replacement_text.encode('utf-8'),
                           replacement_line[replacement_end_column - 1:]))

            if replacement_lines:
                comment_text = (
                    '%s\n'
                    '\n'
                    'Suggested replacement:\n'
                    '```%s```'
                    % (comment_text,
                       b'\n'.join(replacement_lines).decode('utf-8').strip())
                )

            f.comment(text=comment_text,
                      first_line=first_line,
                      num_lines=num_lines,
                      start_column=comment.get('column'),
                      severity=comment.get('level'),
                      error_code=comment.get('code'),
                      rich_text=True)
