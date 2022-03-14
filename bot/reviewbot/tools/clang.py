"""Review Bot tool to run Clang."""

from __future__ import unicode_literals

import os
import shlex

try:
    # Python 3.x
    from plistlib import load as plist_load
except ImportError:
    # Python 2.x
    from plistlib import readPlist as plist_load

from reviewbot.config import config
from reviewbot.tools.base import BaseTool, FullRepositoryToolMixin
from reviewbot.utils.filesystem import make_tempfile
from reviewbot.utils.process import execute


class ClangTool(FullRepositoryToolMixin, BaseTool):
    """Review Bot tool to run clang --analyze."""

    name = 'Clang Static Analyzer'
    version = '1.0'
    description = 'Checks code using clang --analyze.'
    timeout = 30

    exe_dependencies = ['clang']
    file_patterns = [
        '*.c', '*.cc', '*.cpp', '*.cxx', '*.c++',
        '*.m', '*.mm',
    ]

    options = [
        {
            'name': 'cmdline_args',
            'field_type': 'django.forms.CharField',
            'default': '',
            'field_options': {
                'label': 'Clang command-line arguments',
                'help_text': (
                    'Any additional arguments to include on the command line '
                    'when invoking clang --analyze. Used primarily to set '
                    'include paths.'
                ),
                'required': False,
            },
        },
    ]

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
        configured_args = settings.get('cmdline_args', '').strip()

        cmd = [
            config['exe_paths']['clang'],
            '-S',
            '--analyze',
            '-Xanalyzer',
            '-analyzer-output=plist',
        ]

        if configured_args:
            cmd += shlex.split(configured_args)

        return cmd

    def handle_file(self, f, path, base_command, **kwargs):
        """Perform a review of a single file.

        Args:
            f (reviewbot.processing.review.File):
                The file to process.

            path (unicode):
                The local path to the patched file to review.

            base_command (list of unicode):
                The base command used to run clang.

            **kwargs (dict, unused):
                Additional keyword arguments.
        """
        outfile = make_tempfile()
        command = list(base_command)

        if path.endswith('.m'):
            command.append('-ObjC')
        elif path.endswith('.mm'):
            command.append('-ObjC++')

        command += [path, '-o', outfile]

        output = execute(command, ignore_errors=True)

        # Check if the file exists. If it doesn't, then the code didn't
        # compile.
        if os.path.exists(outfile):
            try:
                with open(outfile, 'rb') as fp:
                    results = plist_load(fp)
            except Exception as e:
                self.logger.error('Unable to load clang plist output file '
                                  '%s: %s',
                                  outfile, e)
                return

            for diagnostic in results['diagnostics']:
                filename = results['files'][diagnostic['location']['file']]

                if filename == f.dest_file:
                    range_info = self._find_range(diagnostic)

                    f.comment(diagnostic['description'],
                              first_line=range_info['first_line'],
                              num_lines=range_info['num_lines'],
                              start_column=range_info['start_column'])
        else:
            # The file did not compile. Show the output.
            f.comment('Clang could not analyze this file, due to the '
                      'following errors:\n'
                      '\n'
                      '```\n'
                      '%s\n'
                      '```'
                      % output.strip(),
                      first_line=None,
                      rich_text=True)

    def _find_range(self, diagnostic):
        """Find and return the range of lines/columns for the error.

        Args:
            diagnostic (dict):
                The diagnostic to find the line numbers for.

        Returns:
            dict:
            A dictionary of range information:
        """
        for path_node in reversed(diagnostic.get('path', [])):
            # Ranges will generally have up to 2 entries (that we've seen).
            #
            # The first corresponds to the "^"/"^~~~" indicator, pointing to
            # the source of the error/warning.
            #
            # The second, if available, corresponds to the "~~~~~~"
            # indicator.
            #
            # We're only showing the first range.
            if path_node['kind'] == 'event' and 'ranges' in path_node:
                ranges = path_node['ranges']
                line_range1 = ranges[0]
                line_range2 = ranges[-1]
                range1 = line_range1[0]
                range2 = line_range2[1]
                first_line = range1['line']
                last_line = range2['line']

                return {
                    'first_line': first_line,
                    'num_lines': last_line - first_line + 1,
                    'start_column': range1['col'],
                }

        location = diagnostic['location']

        return {
            'first_line': location['line'],
            'num_lines': 1,
            'start_column': location['col'],
        }
