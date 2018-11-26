"""Review Bot tool to run pydocstyle."""

from __future__ import unicode_literals

from reviewbot.tools import Tool
from reviewbot.utils.process import execute, is_exe_in_path


class PydocstyleTool(Tool):
    """Review Bot tool to run pydocstyle."""

    name = 'pydocstyle'
    version = '1.0'
    description = 'Checks Python code for docstring conventions.'
    timeout = 30
    options = [
        {
            'name': 'ignore',
            'field_type': 'django.forms.CharField',
            'default': '',
            'field_options': {
                'label': 'Ignore',
                'help_text': ('A comma-separated list of errors or prefixes '
                              'to ignore. For example, passing D1 will '
                              'ignore all error codes beginning with "D1" '
                              '(i.e. D1, D10). The list will be passed '
                              'to the --ignore command line argument. '
                              'If no arguments are specified, pydocstyle '
                              'will default to PEP 257 convention.'),
                'required': False,
            },
        },
    ]

    def check_dependencies(self):
        """Verify that the tool's dependencies are installed.

        Returns:
            bool:
            True if all dependencies for the tool are satisfied. If this
            returns False, the worker will not be listed for this Tool's queue,
            and a warning will be logged.
        """
        return is_exe_in_path('pydocstyle')

    def handle_file(self, f, settings):
        """Perform a review of a single file.

        Args:
            f (reviewbot.processing.review.File):
                The file to process.

            settings (dict):
                Tool-specific settings.
        """
        if not f.dest_file.lower().endswith('.py'):
            # Ignore the file.
            return

        path = f.get_patched_file_path()

        if not path:
            return

        self.output = execute(
            [
                'pydocstyle',
                '--ignore=%s' % settings['ignore'],
                path,
            ],
            ignore_errors=True)

        for line in filter(None, self.output.split(path + ':')):
            try:
                line_num, message = line.split(':', 1)
                line_num = line_num.split()
                f.comment(message.strip(), int(line_num[0]))
            except Exception:
                pass
