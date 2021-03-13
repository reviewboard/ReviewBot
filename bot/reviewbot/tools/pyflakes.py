from __future__ import unicode_literals

import re

from reviewbot.tools import Tool
from reviewbot.utils.process import execute, is_exe_in_path


class PyflakesTool(Tool):
    """Review Bot tool to run pyflakes."""

    name = 'Pyflakes'
    version = '1.0'
    description = 'Checks Python code for errors using Pyflakes.'
    timeout = 30

    LINE_RE = re.compile(
        r'^(?P<filename>[^:]+)(:(?P<linenum>\d+)(:\d+)?)?: (?P<msg>.*)')

    def check_dependencies(self):
        """Verify the tool's dependencies are installed.

        Returns:
            bool:
            True if all dependencies for the tool are satisfied. If this
            returns False, the worker will not listen for this Tool's queue,
            and a warning will be logged.
        """
        return is_exe_in_path('pyflakes')

    def handle_file(self, f, settings={}):
        """Perform a review of a single file.

        Args:
            f (reviewbot.processing.review.File):
                The file to process.

            settings (dict, unused):
                Tool-specific settings.
        """
        if not f.dest_file.endswith('.py'):
            # Ignore the file.
            return

        path = f.get_patched_file_path()

        if not path:
            return

        output, errors = execute(['pyflakes', path],
                                 split_lines=True,
                                 ignore_errors=True,
                                 return_errors=True)

        # pyflakes can output one of 3 things:
        #
        # 1. A lint warning about code, which looks like:
        #
        #    filename:linenum:offset: msg
        #
        # 2. An unexpected error:
        #
        #    filename: msg
        #
        # 3. A syntax error, which will look like one of the following forms:
        #
        #    1. filename:linenum:offset: msg
        #       code line
        #       marker ("... ^")
        #
        #    2. filename:linenum: msg
        #       code line
        #
        # We need to handle each case. Fortunately, only #1 is sent to
        # stdout, and the rest to stderr. We can easily pattern match based
        # on where the lines came from.
        LINE_RE = self.LINE_RE

        for line in output:
            m = LINE_RE.match(line)

            if m:
                try:
                    linenum = int(m.group('linenum'))
                except ValueError:
                    # This isn't actually an info line. No idea what it is.
                    # Skip it.
                    continue

                # Report on the lint message.
                f.comment(m.group('msg'), linenum)

        i = 0

        while i < len(errors):
            m = LINE_RE.match(errors[i])

            if m:
                linenum = m.group('linenum')
                msg = m.group('msg')

                if linenum is None:
                    # This is an unexpected error. Leave a general comment.
                    f.review.general_comment(
                        'pyflakes could not process %s: %s'
                        % (f.dest_file, msg))
                else:
                    # This should be a syntax error.
                    try:
                        linenum = int(linenum)
                    except ValueError:
                        # This isn't actually an info line. This is unexpeted,
                        # but skip it.
                        continue

                    f.comment(msg, linenum)

                    # Skip to the code line.
                    i += 1

                    if i + 1 < len(errors) and errors[i + 1].strip() == '^':
                        # This is a match offset line. Skip it.
                        i += 1

            # Process the next error line.
            i += 1
