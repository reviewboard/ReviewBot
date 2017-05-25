from __future__ import unicode_literals

import plistlib
import shlex

from reviewbot.tools import RepositoryTool
from reviewbot.utils.filesystem import make_tempfile
from reviewbot.utils.process import execute, is_exe_in_path


class ClangTool(RepositoryTool):
    """Review Bot tool to run clang --analyze."""

    name = 'Clang Static Analyzer'
    version = '1.0'
    description = 'Checks code using clang --analyze.'
    timeout = 30
    options = [
        {
            'name': 'cmdline_args',
            'field_type': 'django.forms.CharField',
            'default': '',
            'field_options': {
                'label': 'Clang command-line arguments',
                'help_text': 'Any additional arguments to include on the '
                             'command-line when invoking clang --analyze. '
                             'Used primarily to set include paths.',
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
        return is_exe_in_path('clang')

    def handle_file(self, f, settings):
        """Perform a review of a single file.

        Args:
            f (reviewbot.processing.review.File):
                The file to process.

            settings (dict):
                Tool-specific settings.
        """
        filename = f.dest_file.lower()

        if not filename.endswith(('.c', '.cpp', '.cxx', '.m', '.mm')):
            # Ignore the file.
            return

        path = f.get_patched_file_path()

        if not path:
            return

        additional_args = []
        configured_args = settings.get('cmdline_args')

        if configured_args:
            additional_args = shlex.split(configured_args)

        outfile = make_tempfile()

        command = ['clang', '-S', '--analyze']

        if filename.endswith('.m'):
            command.append('-ObjC')
        elif filename.endswith('.mm'):
            command.append('-ObjC++')

        command += additional_args
        command += [path, '-Xanalyzer', '-analyzer-output=plist', '-o',
                    outfile]

        self.output = execute(command, ignore_errors=True)

        results = plistlib.readPlist(outfile)

        for diagnostic in results['diagnostics']:
            file_index = diagnostic['location']['file']
            filename = results['files'][file_index]

            if filename != f.dest_file:
                continue

            line, num_lines = self._find_linenums(diagnostic)
            f.comment(diagnostic['description'], line, num_lines)

    def _find_linenums(self, diagnostic):
        """Find and return the given line numbers.

        Args:
            diagnostic (dict):
                The diagnostic to find the line numbers for.

        Returns:
            tuple of int:
            A 2-tuple, consisting of the line number and the number of lines
            covered by the given diagnostic.
        """
        for path_node in diagnostic.get('path', []):
            if path_node['kind'] == 'event' and 'ranges' in path_node:
                line_range = path_node['ranges'][0]
                first_line = line_range[0]['line']
                last_line = line_range[1]['line']

                return (first_line, last_line - first_line + 1)

        first_line = diagnostic['location']['line']
        return (first_line, 1)
