"""Review Bot tool to run Go Tools."""

from __future__ import unicode_literals

import json
import os
import re
from collections import OrderedDict

import six

from reviewbot.config import config
from reviewbot.tools.base import BaseTool, FullRepositoryToolMixin
from reviewbot.utils.process import execute


class GoTool(FullRepositoryToolMixin, BaseTool):
    """Review Bot tool to run Go Tools."""

    name = 'GoTool'
    version = '1.0'
    description = (
        'Checks Go code for test errors using built-in Go tools "go test", '
        'and "go vet".'
    )
    timeout = 90

    exe_dependencies = ['go']
    file_patterns = ['*.go']

    options = [
        {
            'name': 'test',
            'field_type': 'django.forms.BooleanField',
            'default': False,
            'field_options': {
                'label': 'Run tests',
                'required': False,
                'help_text': 'Run unit tests using "go test".',
            },
        },
        {
            'name': 'vet',
            'field_type': 'django.forms.BooleanField',
            'default': True,
            'field_options': {
                'label': 'Vet code',
                'required': False,
                'help_text': 'Run lint checks against code using "go vet".',
            },
        },
    ]

    PACKAGE_LINE_RE = re.compile(r'^# (.*)$')

    VET_ERROR_RE = re.compile(
        r'^(vet: )?(?P<path>.*\.go):(?P<linenum>\d+):(?P<column>\d+): '
        r'(?P<text>.*)$',
        re.M)

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
            super(GoTool, self).get_can_handle_file(review_file, **kwargs) and
            not review_file.dest_file.lower().endswith('_test.go')
        )

    def handle_files(self, files, review, **kwargs):
        """Perform a review of all files.

        Args:
            files (list of reviewbot.processing.review.File):
                The files to process.

            review (reviewbot.processing.review.Review):
                The review that comments will apply to.

            **kwargs (dict):
                Additional keyword arguments.
        """
        packages = set()
        patched_files_map = {}

        super(GoTool, self).handle_files(files=files,
                                         packages=packages,
                                         patched_files_map=patched_files_map,
                                         **kwargs)

        settings = self.settings
        run_test = settings.get('test', False)
        run_vet = settings.get('vet', False)

        for package in packages:
            if run_test:
                self.run_go_test(package, review)

            if run_vet:
                self.run_go_vet(package, patched_files_map)

    def handle_file(self, f, path, packages, patched_files_map, **kwargs):
        """Perform a review of a single file.

        Args:
            f (reviewbot.processing.review.File):
                The file to process.

            path (unicode):
                The local path to the patched file to review.

            packages (set of unicode):
                A set of all package names. This function will add the file's
                package to this set.

            patched_files_map (dict):
                A mapping of paths to files being reviewed. This function
                will add the path and file to this map.

            **kwargs (dict, unused):
                Additional keyword arguments.
        """
        packages.add(os.path.dirname(path))
        patched_files_map[path] = f

    def run_go_test(self, package, review):
        """Execute 'go test' on a given package

        Args:
            package (unicode):
                Name of the go package.

            review (reviewbot.processing.review.Review):
                The review object.
        """
        output = execute(
            [
                config['exe_paths']['go'],
                'test',
                '-json',
                '-vet=off',
                './%s' % package,
            ],
            split_lines=True,
            ignore_errors=True)

        test_results = OrderedDict()
        found_json_errors = False

        for line in output:
            try:
                entry = json.loads(line)
            except ValueError:
                found_json_errors = True
                continue

            if 'Test' in entry:
                action = entry['Action']

                if action in ('fail', 'output'):
                    test_name = entry['Test']
                    package = entry['Package']

                    if test_name not in test_results:
                        test_results[test_name] = {
                            'failed': False,
                            'output': [],
                            'package': package,
                        }

                    test_result = test_results[test_name]

                    if action == 'output':
                        test_result['output'].append(entry['Output'])
                    elif action == 'fail':
                        test_result['failed'] = True

        if test_results:
            for test_name, test_result in six.iteritems(test_results):
                if test_result['failed']:
                    review.general_comment(
                        '%s failed in the %s package:\n'
                        '\n'
                        '```%s```'
                        % (test_name,
                           test_result['package'],
                           ''.join(test_result['output']).strip()),
                        rich_text=True)
        elif found_json_errors:
            review.general_comment(
                'Unable to run `go test` on the %s package:\n'
                '\n'
                '```%s```'
                % (package, ''.join(output).strip()),
                rich_text=True)

    def run_go_vet(self, package, patched_files_map):
        """Execute 'go vet' on a given package

        Args:
            package (unicode):
                Name of the go package.

            patched_files_map (dict):
                Mapping from filename to
                :py:class:`~reviewbot.processing.review.File` to add comments.
        """
        # Ideally, we would use -json, but unfortunately `go vet` doesn't
        # always respect this for all errors. Rather than checking for both
        # JSON output and non-JSON output, we'll just parse the usual way.
        output = execute(
            [
                config['exe_paths']['go'],
                'vet',
                './%s' % package,
            ],
            with_errors=True,
            ignore_errors=True)

        for m in self.VET_ERROR_RE.finditer(output):
            path = m.group('path')
            linenum = int(m.group('linenum'))
            column = int(m.group('column'))
            text = m.group('text')

            f = patched_files_map.get(path)

            if f is None:
                self.logger.error('Could not find path "%s" in patched '
                                  'file map %r',
                                  path, patched_files_map)
            else:
                f.comment(text=text,
                          first_line=linenum,
                          start_column=column)
