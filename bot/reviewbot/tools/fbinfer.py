"""Review Bot tool to run FBInfer."""

from __future__ import unicode_literals

import json
import logging
import shlex

from reviewbot.tools import RepositoryTool
from reviewbot.utils.process import execute, is_exe_in_path


logger = logging.getLogger(__name__)


class FBInferTool(RepositoryTool):
    """Review Bot tool to run FBInfer."""

    name = 'FBInfer'
    version = '1.0'
    description = ('Checks code for errors using FBInfer, a tool for static '
                   'Android, Java, C, C++, and iOS/Objective-C code analysis.')
    timeout = 90
    options = [
        {
            'name': 'build_type',
            'field_type': 'django.forms.ChoiceField',
            'field_options': {
                'label': 'Select Build Type',
                'help_text': 'Choose how the project will be compiled.',
                'choices': (
                    ('./gradlew', 'Android/Gradle with Wrapper'),
                    ('ant', 'Apache Ant'),
                    ('buck build', 'Buck'),
                    ('clang -c', 'C/Objective-C'),
                    ('cmake', 'CMake'),
                    ('gradle', 'Gradle'),
                    ('xcodebuild', 'iOS/XCode'),
                    ('javac', 'Java'),
                    ('make', 'Make'),
                    ('mvn', 'Maven'),
                ),
            },
        },
        {
            'name': 'build_target',
            'field_type': 'django.forms.CharField',
            'default': '',
            'field_options': {
                'label': 'Build Target',
                'required': False,
                'help_text': (
                    'Include a build target if required to successfully build '
                    'the project. (e.g. pass in the "build" parameter for a '
                    'gradle compilation or a target for a buck compilation)'
                ),
            },
        },
        {
            'name': 'xcode_configuration',
            'field_type': 'django.forms.CharField',
            'default': '',
            'field_options': {
                'label': 'XCode Configuration',
                'required': False,
                'help_text': ('Include any additional configuration options '
                              'for the Xcode -configuration flag.'),
            },
        },
        {
            'name': 'sdk',
            'field_type': 'django.forms.CharField',
            'default': '',
            'field_options': {
                'label': 'SDK',
                'required': False,
                'help_text': ('Include an SDK required to build a project '
                              'such as "iphonesimulator" for iOS.'),
            },
        },
    ]

    # Tuple of builds that do not require a path.
    multi_file_build_types = (
        'ant',
        'buck build',
        'cmake',
        'gradle',
        './gradlew',
        'make',
        'mvn',
        'xcodebuild',
    )

    def check_dependencies(self):
        """Verify the tool's dependencies are installed.

        Returns:
            bool:
            True if all dependencies for the tool are satisfied. If this
            returns False, the worker will not listen for this Tool's queue,
            and a warning will be logged.
        """
        return is_exe_in_path('infer')

    def handle_files(self, files, settings):
        """Perform a review of all files.

        Args:
            files (list of reviewbot.processing.review.File):
                The files to process.

            settings (dict):
                Tool-specific settings.
        """
        self.build_type = settings['build_type']

        if self.build_type in self.multi_file_build_types:
            self.run_multi_file_build(files, settings)

            for f in files:
                self.report_file(f)
        else:
            for f in files:
                self.run_single_file_build(f)
                self.report_file(f)

    def report_file(self, f):
        """Report infer results for a given file.

        Args:
            f (reviewbot.processing.review.File):
                The file to process.
        """
        path = f.get_patched_file_path()

        if not path:
            return

        try:
            with open('infer-out/report.json', 'r') as fp:
                json_data = json.load(fp)
                for entry in json_data:
                    if path == entry['file']:
                        f.comment('Bug Type: %(bug_type_hum)s\n'
                                  '%(severity)s %(qualifier)s'
                                  % entry,
                                  first_line=entry['line'],
                                  rich_text=True)
        except Exception as e:
            logger.exception('JSON file could not be opened/loaded: %s', e)

    def run_multi_file_build(self, files, settings):
        """Perform execution of FBInfer run on a multi-file build

        Args:
            files (list of reviewbot.processing.review.File):
                The files to process.

            settings (dict):
                Tool-specific settings.
        """
        # CMake requires a compilation before analysis.
        if self.build_type == 'cmake':
            try:
                execute([
                    'infer',
                    'compile',
                    '--',
                    self.build_type,
                    '.',
                ])

                # After compilation, update build_type from CMake to Make.
                # FBInfer uses Make in `infer run` to do its analysis.
                self.build_type = 'make'
            except Exception as e:
                logger.exception('FBInfer compile command failed with build '
                                 'type: %s %s', self.build_type, e)

        # Build the infer command to execute.
        infer_cmd = [
            'infer',
            'run',
            '--',
        ]

        # Append the build type.
        infer_cmd += shlex.split(self.build_type)

        # Check for a specified build target.
        if settings['build_target'] != '':
            if self.build_type == 'xcodebuild':
                infer_cmd.append('-target')
            infer_cmd.append(settings['build_target'])

        # Append necessary configurations and SDKs for Xcode.
        if settings['xcode_configuration'] != '':
            infer_cmd += [
                '-configuration',
                settings['xcode_configuration']
            ]

        if settings['sdk'] != '':
            infer_cmd += [
                '-sdk',
                settings['sdk']
            ]

        try:
            execute(infer_cmd)
        except Exception as e:
            logger.exception('FBInfer run command failed with build type: '
                             '%s %s', self.build_type, e)

    def run_single_file_build(self, f):
        """Perform execution of FBInfer run on a single file

        Args:
            f (reviewbot.processing.review.File):
                The file to process.
        """
        path = f.get_patched_file_path()

        if not path:
            return

        try:
            execute(['infer', 'run', '--'] +
                    shlex.split(self.build_type) +
                    [path])
        except Exception as e:
            logger.exception('FBInfer run command failed with file: '
                             '%s %s', path, e)
