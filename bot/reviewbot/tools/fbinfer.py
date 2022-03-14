"""Review Bot tool to run FBInfer."""

from __future__ import unicode_literals

import json
import os
import shlex

from reviewbot.config import config
from reviewbot.tools.base import BaseTool, FullRepositoryToolMixin
from reviewbot.utils.process import execute


class FBInferTool(FullRepositoryToolMixin, BaseTool):
    """Review Bot tool to run FBInfer."""

    name = 'FBInfer'
    version = '1.0'
    description = (
        'Checks code for errors using FBInfer, a tool for static Android, '
        'Java, C, C++, and iOS/Objective-C code analysis.'
    )
    timeout = 90

    exe_dependencies = ['infer']

    options = [
        {
            'name': 'build_type',
            'field_type': 'django.forms.ChoiceField',
            'field_options': {
                'label': 'Build system',
                'help_text': 'Choose how the project will be compiled.',
                'choices': (
                    ('./gradlew', 'Android/Gradle with Wrapper (./gradlew)'),
                    ('ant', 'Apache Ant (ant)'),
                    ('buck build', 'Buck (buck build)'),
                    ('clang -c', 'Clang (clang -c)'),
                    ('cmake', 'CMake (cmake)'),
                    ('gradle', 'Gradle (gradle)'),
                    ('javac', 'Java (javac)'),
                    ('make', 'Make (make)'),
                    ('mvn', 'Maven (mvn)'),
                    ('xcodebuild', 'XCode (xcodebuild)'),
                ),
            },
        },
        {
            'name': 'build_target',
            'field_type': 'django.forms.CharField',
            'default': '',
            'field_options': {
                'label': 'Build target',
                'required': False,
                'help_text': (
                    'The name of the target to build, if the build system '
                    'needs one or is capable of building multiple targets.'
                ),
            },
        },
        {
            'name': 'xcode_configuration',
            'field_type': 'django.forms.CharField',
            'default': '',
            'field_options': {
                'label': 'XCode configuration',
                'required': False,
                'help_text': (
                    'Any additional configuration options needed for a '
                    'XCode build (equivalent to the -configuration flag). '
                    'This is ignored for non-XCode builds'
                ),
            },
        },
        {
            'name': 'sdk',
            'field_type': 'django.forms.CharField',
            'default': '',
            'field_options': {
                'label': 'XCode SDK',
                'required': False,
                'help_text': (
                    'Include an XCode SDK required to build a project '
                    'such as "iphonesimulator" for iOS. This is ignored for '
                    'non-XCode builds.'
                )
            },
        },
    ]

    # Tuple of builds that do not require a path.
    MULTI_FILE_BUILD_TYPES = {
        './gradlew',
        'ant',
        'buck build',
        'cmake',
        'gradle',
        'make',
        'mvn',
        'xcodebuild',
    }

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
        build_type = settings['build_type']
        build_target = settings.get('build_target', '').strip()

        if build_type == 'cmake':
            # CMake is treated specially. We'll be running `cmake` in
            # _run_multi_file_build() using `fbinfer compile`, and then we'll
            # switch to `make`. We're building that second-stage command, so
            # change to `make` here.
            build_type = 'make'

        cmd = [
            config['exe_paths']['infer'],
            'run',
            '--no-progress-bar',
            '--',
        ] + shlex.split(build_type)

        if build_type == 'xcodebuild':
            xcode_configuration = \
                settings.get('xcode_configuration', '').strip()
            xcode_sdk = settings.get('sdk', '').strip()

            if build_target:
                cmd += ['-target', build_target]

            if xcode_configuration:
                cmd += ['-configuration', xcode_configuration]

            if xcode_sdk:
                cmd += ['-sdk', xcode_sdk]
        else:
            if build_target:
                cmd.append(build_target)

        return cmd

    def handle_files(self, files, review, base_command, **kwargs):
        """Perform a review of all files.

        Args:
            files (list of reviewbot.processing.review.File):
                The files to process.

            review (reviewbot.processing.review.Review):
                The review being populated.

            base_command (list of unicode):
                The base command used to run infer.

            **kwargs (dict):
                Additional keyword arguments.
        """
        build_type = self.settings['build_type']

        if build_type == 'cmake':
            # CMake has an extra compilation step before we can run
            # `fbinfer run`. Do that here.
            try:
                execute([
                    config['exe_paths']['infer'],
                    'compile',
                    '--',
                    build_type,
                    '.',
                ])
            except Exception as e:
                self.logger.exception(
                    'FBInfer was unable to compile CMake build for "%s": %s',
                    os.getcwd(), e)

                review.general_comment(
                    'FBInfer was unable to build this project using CMake.',
                    rich_text=True)

                return

        if build_type in self.MULTI_FILE_BUILD_TYPES:
            try:
                execute(base_command,
                        ignore_errors=True,
                        return_errors=True)
            except Exception as e:
                self.logger.exception(
                    'FBInfer was unable to build "%s" using %s: %s',
                    os.getcwd(), build_type, e)

                review.general_comment(
                    'FBInfer was unable to build this project:\n',
                    rich_text=True)

                return

            report = self._load_report([
                _file.patched_file_path
                for _file in files
            ])
        else:
            report = []

            super(FBInferTool, self).handle_files(files=files,
                                                  base_command=base_command,
                                                  report=report,
                                                  review=review,
                                                  **kwargs)

        cwd = os.getcwd()
        paths_to_files = {
            os.path.relpath(_file.patched_file_path, cwd): _file
            for _file in files
        }

        for entry in sorted(report,
                            key=lambda _entry: (_entry['file'],
                                                _entry['line'],
                                                _entry['column'])):
            # We should be able to trust that this file is in the map above,
            # since we've previously filtered reports by eligible file paths.
            f = paths_to_files[entry['file']]

            column = entry['column']

            if column == -1:
                # The error pertains to the whole line.
                column = None

            f.comment(text=entry['qualifier'],
                      severity=entry['severity'],
                      error_code=entry['bug_type_hum'],
                      first_line=entry['line'],
                      start_column=column,
                      rich_text=True)

    def handle_file(self, f, path, review, base_command, report, **kwargs):
        """Perform a review of a single file.

        If this is part of a multi-file build, the results for this file from
        that build will be reported. If not a multi-file build, then
        :command:`infer` will be run on this file before reporting results.

        Args:
            f (reviewbot.processing.review.File):
                The file to process.

            path (unicode):
                The local path to the patched file to review.

            review (reviewbot.processing.review.Review):
                The review being populated.

            base_command (list of unicode):
                The base command used to run infer.

            report (list of dict):
                The report to append to.

            **kwargs (dict, unused):
                Additional keyword arguments.
        """
        try:
            execute(base_command + [path],
                    with_errors=True,
                    ignore_errors=True)
        except Exception as e:
            self.logger.exception(
                'FBInfer run command failed to build file "%s" using '
                '"%s": %s',
                path, base_command, e)

            review.general_comment(
                'FBInfer was unable to build `%s`.' % path,
                rich_text=True)

            return

        report += self._load_report([path])

    def _load_report(self, paths):
        """Return report entries for the provided paths.

        This will load the JSON report from FBInfer and filter it down to any
        results that pertain to the provided list of paths.

        Args:
            paths (list of unicode):
                The list of absolute paths to files used to filter down
                the report.

        Returns:
            list of dict:
            The filtered report entries.
        """
        # The report will have paths relative to the root of the tree, so
        # we'll need to normalize our paths so we can compare them.
        cwd = os.getcwd()
        paths = {
            os.path.relpath(_path, cwd)
            for _path in paths
        }

        # FullRepositoryToolMixin will put us in the right directory for
        # this file. We can generate an absolute path from there.
        report_filename = os.path.join(cwd, 'infer-out', 'report.json')

        if not os.path.exists(report_filename):
            return []

        try:
            with open(report_filename, 'r') as fp:
                return [
                    _entry
                    for _entry in json.load(fp)
                    if _entry['file'] in paths
                ]
        except Exception as e:
            self.logger.exception('Infer report file (%s) could not be '
                                  'loaded: %s',
                                  report_filename, e)
            return []
