"""Review Bot tool to run Go Tools."""

from __future__ import unicode_literals

import json
import logging
import os
import re
import six

from reviewbot.tools import RepositoryTool
from reviewbot.utils.process import execute, is_exe_in_path


logger = logging.getLogger(__name__)


class GoTool(RepositoryTool):
    """Review Bot tool to run Go Tools."""

    name = 'GoTool'
    version = '1.0'
    description = ('Checks Go code for test errors using built-in Go tools '
                   '"go test", and "go vet".')
    timeout = 90
    options = [
        {
            'name': 'test',
            'field_type': 'django.forms.BooleanField',
            'default': False,
            'field_options': {
                'label': 'Run Tests',
                'required': False,
            },
        },
        {
            'name': 'vet',
            'field_type': 'django.forms.BooleanField',
            'default': True,
            'field_options': {
                'label': 'Vet Code',
                'required': False,
            },
        },
    ]
    package_regex = re.compile(r'^[#].*')

    def check_dependencies(self):
        """Verify the tool's dependencies are installed.

        Returns:
            bool:
            True if all dependencies for the tool are satisfied. If this
            returns False, the worker will not listen for this Tool's queue,
            and a warning will be logged.
        """
        return is_exe_in_path('go')

    def handle_files(self, files, settings):
        """Perform a review of all files.

        Args:
            files (list of reviewbot.processing.review.File):
                The files to process.

            settings (dict):
                Tool-specific settings.
        """
        packages = set()
        patched_file_dict = {}

        # Reference to a review object so that a general comment can be
        # made in the 'go test' command.
        review_obj = files[0].review

        for index, f in enumerate(files):
            # Store a review object, but only once.
            if index == 0:
                review_obj = f.review

            filename = f.dest_file.lower()

            if not filename.endswith('.go'):
                # Ignore the file.
                continue

            if filename.endswith('_test.go'):
                # Ignore the test file.
                continue

            path = f.get_patched_file_path()

            if not path:
                continue

            # Add package to packages set if it does not already exist.
            packages.add(os.path.dirname(path))

            patched_file_dict[path] = f

        for package in packages:
            if settings['test']:
                self.run_go_test(package, review_obj)

            if settings['vet']:
                self.run_go_vet(package, patched_file_dict)

    def run_go_test(self, package, review_obj):
        """Execute 'go test' on a given package

        Args:
            package (unicode):
                Name of the go package.

            review_obj (reviewbot.processing.review.Review):
                The review object.
        """
        try:
            output = execute(
                [
                    'go',
                    'test',
                    '-json',
                    '-vet=off',
                    './%s' % package,
                ],
                split_lines=True,
                ignore_errors=True)

            formatted_output = '[%s]' % ','.join(output)
            json_data = json.loads(formatted_output)

            for entry in json_data:
                if entry['Action'] == 'fail' and 'Test' in entry:
                    test = entry['Test']
                    review_obj.general_comment('%s failed in the %s package.'
                                               % (test, package))
        except Exception as e:
            logger.exception('Go test execution failed for package'
                             '%s: %s', package, e)

    def run_go_vet(self, package, patched_file_dict):
        """Execute 'go vet' on a given package

        Args:
            package (unicode):
                Name of the go package.

            patched_file_dict (dict):
                Mapping from filename to
                :py:class:`~reviewbot.processing.review.File` to add comments.
        """
        try:
            output = execute(
                [
                    'go',
                    'vet',
                    '-json',
                    './%s' % package,
                ])

            package_path = output.split('\n', 1)[0]

            if package_path.startswith('# '):
                package_path = package_path[len('# '):]

            cleaned_output = self.package_regex.sub('', output)
            json_data = json.loads(cleaned_output)

            # Sample JSON data output:
            # {
            #     "...path_to_package/boolexpr": {
            #         "bools": [
            #             {
            #                 "posn": "...path_to_package/bool-expr.go:10:14",
            #                 "message": "suspect or: i != 0 || i != 1"
            #             },
            #             ...additional occurrences of bool errors
            #         ],
            #         "loopclosure": [ ... ]
            #     }
            # }
            if package_path in json_data:
                for i, entry in six.iteritems(json_data[package_path]):
                    for key in entry:
                        filename, line_num, col_num = \
                            os.path.basename(key['posn']).split(':', 2)
                        file_path = os.path.join(package, filename)
                        message = key['message']
                        f = patched_file_dict[file_path]
                        f.comment('Error: %s' % message, int(line_num))
        except Exception as e:
            logger.exception('Go vet execution failed for package'
                             '%s: %s', package, e)
