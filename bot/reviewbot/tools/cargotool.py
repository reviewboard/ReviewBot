"""Review Bot tool to run Cargo commands."""

from __future__ import unicode_literals

import json
import os
import re

from reviewbot.config import config
from reviewbot.tools.base import BaseTool, FullRepositoryToolMixin
from reviewbot.utils.process import execute


class CargoTool(FullRepositoryToolMixin, BaseTool):
    """Review Bot tool to run Cargo Commands."""

    name = 'CargoTool'
    version = '1.0'
    description = (
        'Checks Rust code for linting and test errors using built-in Rust '
        'tools "cargo clippy", and "cargo test".'
    )
    timeout = 120

    exe_dependencies = ['cargo', 'cargo-clippy']
    file_patterns = ['*.rs']

    options = [
        {
            'name': 'clippy',
            'field_type': 'django.forms.BooleanField',
            'default': True,
            'field_options': {
                'label': 'Check and lint code',
                'required': False,
                'help_text': (
                    'Compile using "cargo clippy", checking for errors.'
                ),
            },
        },
        {
            'name': 'test',
            'field_type': 'django.forms.BooleanField',
            'default': False,
            'field_options': {
                'label': 'Run tests',
                'required': False,
                'help_text': 'Run unit tests using "cargo test".',
            },
        },
    ]

    TEST_GROUP_RE = re.compile(
        r'running (?P<num_tests>[1-9]\d*) tests?\n'
        r'.*?\n'
        r'failures:\n'
        r'(?P<test_output>.+?)\n'
        r'test result: FAILED\. \d+ passed; (?P<num_failed>\d+) failed;',
        re.S)

    TEST_LINES_LIMIT = 100

    def build_base_command(self, **kwargs):
        """Build the base command line used to review files.

        Args:
            **kwargs (dict, unused):
                Additional keyword arguments.

        Returns:
            list of unicode:
            The base command line.
        """
        return [config['exe_paths']['cargo']]

    def handle_files(self, files, review, base_command, **kwargs):
        """Perform a review of all files.

        Args:
            files (list of reviewbot.processing.review.File):
                The files to process.

            review (reviewbot.processing.review.Review):
                The review being populated.

            base_command (list of unicode):
                The base command used to run cargo.

            **kwargs (dict, unused):
                Additional keyword arguments.
        """
        settings = self.settings

        if settings.get('clippy'):
            file_results, found_compiler_error = \
                self.run_cargo_clippy(base_command)

            if file_results:
                super(CargoTool, self).handle_files(files=files,
                                                    file_results=file_results,
                                                    **kwargs)

            if found_compiler_error:
                # We likely won't be able to run tests, so stop now.
                return

        if settings.get('test'):
            self.run_cargo_test(review=review,
                                base_command=base_command)

    def handle_file(self, f, path, file_results, **kwargs):
        """Perform a review of a single file.

        Args:
            f (reviewbot.processing.review.File):
                The file to process.

            path (unicode):
                The local path to the patched file to review.

            file_results (dict):
                Lists of :command:`cargo clippy` results, keyed by local
                temp file path.

            **kwargs (dict, unused):
                Additional keyword arguments.
        """
        try:
            results = file_results[os.path.realpath(path)]
        except KeyError:
            # Nothing was found for this file.
            return

        for result in results:
            try:
                message_data = result['message']
                message = message_data['message']
                severity = message_data['level']
            except KeyError:
                # This wasn't a full error payload. Might have been something
                # else. Skip it.
                continue

            try:
                error_code = message_data['code']['code']
            except (KeyError, TypeError):
                error_code = None

            try:
                spans = sorted(
                    message_data['spans'],
                    key=lambda _span: (_span.get('is_primary'),
                                       _span['line_start'],
                                       _span['column_start'],
                                       _span['column_end'],
                                       _span['line_end']))
                span = spans[0]
                first_line = span.get('line_start')
                start_column = span.get('column_start')

                if first_line is not None:
                    num_lines = span['line_end'] - first_line + 1
                else:
                    num_lines = None
            except (IndexError, KeyError):
                continue

            f.comment(text=message,
                      first_line=first_line,
                      num_lines=num_lines,
                      start_column=start_column,
                      error_code=error_code,
                      severity=severity,
                      rich_text=True)

    def run_cargo_clippy(self, base_command):
        """Run cargo clippy on a codebase.

        This will check for lintian/syntax errors. It won't directly report
        them, but will return payloads information covering all files with
        ``compiler-message`` results that will then be handled in
        :py:meth:`handle_file`.

        Args:
            base_command (list of unicode):
                The base command used to run cargo.

        Returns:
            tuple:
            A 2-tuple containing:

            1. A dictionary mapping absolute file paths to lists of clippy
               result payload dictionaries.
            2. A boolean indicating whether a compiler error was found.
        """
        file_results = {}
        found_compiler_error = {}

        lines = execute(
            base_command + [
                'clippy',
                '-q',
                '--message-format=json',
                '--tests',
            ],
            split_lines=True,
            with_errors=False,
            ignore_errors=True)

        for line in lines:
            try:
                data = json.loads(line)

                if data.get('reason') != 'compiler-message':
                    continue

                # Clippy seems to return "real" (normalized, symlink-followed)
                # paths, which the rest of our logic is based around.
                # However, there's no guarantee it always will, so explicitly
                # convert the path here.
                src_path = os.path.realpath(data['target']['src_path'])
                file_results.setdefault(src_path, []).append(data)

                if (not found_compiler_error and
                    data.get('message', {}).get('level') == 'error'):
                    found_compiler_error = True
            except Exception:
                continue

        return file_results, found_compiler_error

    def run_cargo_test(self, review, base_command):
        """Run cargo test on a codebase.

        THis will run the test suite and parse the results. If unit tests
        failed, a general comment will be left showing up to
        :py:attr:`TEST_LINES_LIMIT` lines of unit test output.

        Args:
            base_command (list of unicode):
                The base command used to run cargo.
        """
        output = execute(
            base_command + [
                '-q',
                'test',
                '--',
                '--test-threads=1',
            ],
            ignore_errors=True)

        # TODO: As of this comment (June 11, 2021), `cargo test` doesn't
        #       support JSON output in released builds (using
        #       --message-format=json), only in nightly builds. It's
        #       documented that this is coming, but we can't depend on it yet.
        #
        #       In the future, when enough time has passed, we should switch
        #       to parsing that. It'll be far less error-prone than this.
        for m in self.TEST_GROUP_RE.finditer(output):
            num_failed = int(m.group('num_failed'))
            test_output = m.group('test_output').strip()

            assert num_failed > 0

            if num_failed == 1:
                message = '1 test failed:'
            else:
                message = '%d tests failed:' % num_failed

            # Filter out any backtrace recommendations.
            test_output_lines = [
                _line
                for _line in test_output.splitlines()
                if not _line.startswith('note: run with `RUST_BACKTRACE=1`')
            ]

            # Cap the output length.
            if len(test_output_lines) > self.TEST_LINES_LIMIT:
                num_lines_removed = \
                    len(test_output_lines) - self.TEST_LINES_LIMIT

                test_output_lines = (
                    test_output_lines[:self.TEST_LINES_LIMIT] +
                    ['<%d lines removed>' % num_lines_removed]
                )

            test_output = '\n'.join(test_output_lines)

            review.general_comment(
                '%s\n'
                '\n'
                '```%s```'
                % (message, test_output.strip()),
                rich_text=True)

        if (not self.settings.get('clippy') and
            '\nerror: could not compile' in output):
            # There were issues compiling at least some of the tree. Clippy
            # would catch this, but if it's not running, we'll want to warn
            # the user.
            #
            # If we could use --message-format=json, we could handle those
            # the same way we do with clippy, but we can't do this yet, since
            # we'd also need to have support for the JSON unit test results
            # format (currently only in nightly builds of cargo -- see above).
            review.general_comment(
                'One or more files contained compiler errors. For details, '
                'run `cargo test` locally, or enable Clippy support in '
                'Review Bot.',
                rich_text=True)
