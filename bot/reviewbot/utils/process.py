from __future__ import unicode_literals

import logging
import os
import subprocess
import sys


def execute(command,
            env=None,
            split_lines=False,
            ignore_errors=False,
            extra_ignore_errors=(),
            translate_newlines=True,
            with_errors=True,
            none_on_ignored_error=False):
    """Execute a command and return the output.

    Args:
        command (list of unicode):
            The command to run.

        env (dict, optional):
            The environment variables to use when running the process.

        split_lines (bool, optional):
            Whether to return the output as a list (split on newlines) or a
            single string.

        ignore_errors (bool, optional):
            Whether to ignore non-zero return codes from the command.

        extra_ignore_errors (tuple of int, optional):
            Process return codes to ignore.

        translate_newlines (bool, optional):
            Whether to convert platform-specific newlines (such as \\r\\n) to
            the regular newline (\\n) character.

        with_errors (bool, optional):
            Whether the stderr output should be merged in with the stdout
            output or just ignored.

        none_on_ignored_error (bool, optional):
            Whether to return ``None`` if there was an ignored error (instead
            of the process output).

    Returns:
        unicode or list of unicode:
        Either the output of the process, or a list of lines in the output,
        depending on the value of ``split_lines``.
    """
    if isinstance(command, list):
        logging.debug(subprocess.list2cmdline(command))
    else:
        logging.debug(command)

    if env:
        env.update(os.environ)
    else:
        env = os.environ.copy()

    env['LC_ALL'] = 'en_US.UTF-8'
    env['LANGUAGE'] = 'en_US.UTF-8'

    if with_errors:
        errors_output = subprocess.STDOUT
    else:
        errors_output = subprocess.PIPE

    if sys.platform.startswith('win'):
        p = subprocess.Popen(command,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=errors_output,
                             shell=False,
                             universal_newlines=translate_newlines,
                             env=env)
    else:
        p = subprocess.Popen(command,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=errors_output,
                             shell=False,
                             close_fds=True,
                             universal_newlines=translate_newlines,
                             env=env)
    if split_lines:
        data = p.stdout.readlines()
    else:
        data = p.stdout.read()

    rc = p.wait()

    if rc and not ignore_errors and rc not in extra_ignore_errors:
        raise Exception('Failed to execute command: %s\n%s' % (command, data))

    if rc and none_on_ignored_error:
        return None

    return data


def is_exe_in_path(name):
    """Check whether an executable is in the user's search path.

    Args:
        name (unicode):
            The name of the executable, without any platform-specific
            executable extension. The extension will be appended if necessary.

    Returns:
        boolean:
        True if the executable can be found in the execution path.
    """
    if sys.platform == 'win32' and not name.endswith('.exe'):
        name += '.exe'

    for dir in os.environ['PATH'].split(os.pathsep):
        if os.path.exists(os.path.join(dir, name)):
            return True

    return False
