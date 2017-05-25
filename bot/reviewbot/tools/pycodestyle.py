from __future__ import unicode_literals

from reviewbot.tools import Tool
from reviewbot.utils.process import execute, is_exe_in_path


class PycodestyleTool(Tool):
    """Review Bot tool to run pycodestyle."""

    name = 'pycodestyle'
    version = '1.0'
    description = 'Checks Python code for style errors.'
    timeout = 30
    options = [
        {
            'name': 'max_line_length',
            'field_type': 'django.forms.IntegerField',
            'default': 79,
            'field_options': {
                'label': 'Maximum Line Length',
                'help_text': 'The maximum line length to allow.',
                'required': True,
            },
        },
        {
            'name': 'ignore',
            'field_type': 'django.forms.CharField',
            'default': "",
            'field_options': {
                'label': 'Ignore',
                'help_text': ('A comma-separated list of errors and warnings '
                              'to ignore. This will be passed to the --ignore '
                              'command line argument (e.g. E4,W).'),
                'required': False,
            },
        },
    ]

    def check_dependencies(self):
        """Verify that the tool's dependencies are installed.

        Returns:
            bool:
            True if all dependencies for the tool are satisfied. If this
            returns False, the worker will not listed for this Tool's queue,
            and a warning will be logged.
        """
        return is_exe_in_path('pycodestyle')

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

        output = execute(
            [
                'pycodestyle',
                '--max-line-length=%s' % settings['max_line_length'],
                '--ignore=%s' % settings['ignore'],
                path,
            ],
            split_lines=True,
            ignore_errors=True)

        for line in output:
            try:
                # Strip off the filename, since it might have colons in it.
                line = line[len(path) + 1:]

                line_num, column, message = line.split(':', 2)
                f.comment(message.strip(), int(line_num))
            except:
                pass
