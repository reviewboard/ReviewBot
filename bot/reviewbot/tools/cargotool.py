"""Review Bot tool to run Cargo Commands."""

from __future__ import unicode_literals

from collections import defaultdict
import logging

from reviewbot.tools import RepositoryTool
from reviewbot.utils.process import execute, is_exe_in_path


logger = logging.getLogger(__name__)


class CargoTool(RepositoryTool):
    """Review Bot tool to run Cargo Commands."""

    name = 'CargoTool'
    version = '1.0'
    description = ('Checks Rust code for linting and test errors using '
                   'built-in Rust tools "cargo clippy", and "cargo test".')
    timeout = 120
    options = [
        {
            'name': 'clippy',
            'field_type': 'django.forms.BooleanField',
            'default': True,
            'field_options': {
                'label': 'Check and Lint Code',
                'required': False,
            },
        },
        {
            'name': 'test',
            'field_type': 'django.forms.BooleanField',
            'default': False,
            'field_options': {
                'label': 'Run Tests',
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
        return (is_exe_in_path('cargo') and is_exe_in_path('cargo-clippy'))

    def handle_files(self, files, settings):
        """Perform a review of all files.

        Args:
            files (list of reviewbot.processing.review.File):
                The files to process.

            settings (dict):
                Tool-specific settings.
        """
        prefixes = ('error: ', 'warning: ')
        comment_dict = defaultdict(list)

        # Build and execute the cargo clippy command.
        if settings['clippy']:
            try:
                lines = execute(
                    ['cargo', 'clippy'],
                    split_lines=True,
                    ignore_errors=True)

                num_lines = len(lines)

                for i, line in enumerate(lines):
                    if i + 1 >= num_lines:
                        break

                    next_line = lines[i + 1].lstrip()

                    if (line.startswith(prefixes) and
                        next_line.startswith('--> ')):

                        message = line
                        trimmed = next_line.lstrip('--> ')
                        filename, line_num, col_num = trimmed.split(':', 2)

                        comment_dict[filename].append({
                            'line_num': int(line_num),
                            'message': message,
                        })
            except Exception as e:
                logger.exception('cargo clippy failed: %s', e)

        for f in files:
            if not f.dest_file.lower().endswith('.rs'):
                # Ignore the file.
                continue

            path = f.get_patched_file_path()

            if not path:
                continue

            for entry in comment_dict[path]:
                f.comment(entry['message'], entry['line_num'])

        # Build and execute the cargo test command.
        if settings['test']:
            try:
                lines = execute(
                    ['cargo', 'test'],
                    split_lines=True,
                    ignore_errors=True)

                for line in lines:
                    if line.lstrip().startswith('test::'):
                        test_name = line.split('::', 1)[1]
                        f.review.general_comment('Test Failed: %s' % test_name)
            except Exception as e:
                logger.exception('cargo test failed: %s', e)
