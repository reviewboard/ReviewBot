"""Review Bot tool to run pyflakes."""

from __future__ import unicode_literals

import re

from reviewbot.config import config
from reviewbot.tools.base import BaseTool
from reviewbot.utils.process import execute


class PyflakesTool(BaseTool):
    """Review Bot tool to run pyflakes."""

    name = 'Pyflakes'
    version = '1.0'
    description = 'Checks Python code for errors using Pyflakes.'
    timeout = 30

    exe_dependencies = ['pyflakes']
    file_patterns = ['*.py']

    LINE_RE = re.compile(
        r'^(?P<filename>[^:]+)(:(?P<linenum>\d+)(:(?P<column>\d+))?)?:? '
        r'(?P<msg>.*)'
    )

    def build_base_command(self, **kwargs):
        """Build the base command line used to review files.

        Args:
            **kwargs (dict, unused):
                Additional keyword arguments.

        Returns:
            list of unicode:
            The base command line.
        """
        return [config['exe_paths']['pyflakes']]

    def handle_file(self, f, path, base_command, **kwargs):
        """Perform a review of a single file.

        Args:
            f (reviewbot.processing.review.File):
                The file to process.

            path (unicode):
                The local path to the patched file to review.

            base_command (list of unicode):
                The base command used to run pyflakes.

            **kwargs (dict, unused):
                Additional keyword arguments.
        """
        output, errors = execute(base_command + [path],
                                 split_lines=True,
                                 ignore_errors=True,
                                 return_errors=True)

        # pyflakes can output one of 3 things:
        #
        # 1. A lint warning about code, which looks like:
        #
        #    filename:linenum:offset msg
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
                    column = int(m.group('column'))
                except ValueError:
                    # This isn't actually an info line. No idea what it is.
                    # Skip it.
                    continue

                # Report on the lint message.
                f.comment(m.group('msg'),
                          first_line=linenum,
                          start_column=column)

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
                        column = int(m.group('column'))
                    except ValueError:
                        # This isn't actually an info line. This is
                        # unexpected, but skip it.
                        continue

                    f.comment(msg,
                              first_line=linenum,
                              start_column=column)

                    # Skip to the code line.
                    i += 1

                    if i + 1 < len(errors) and errors[i + 1].strip() == '^':
                        # This is a match offset line. Skip it.
                        i += 1

            # Process the next error line.
            i += 1
