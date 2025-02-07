"""Utility functions for Process invocation and management."""

from __future__ import annotations

import os
import subprocess
import sys
from typing import Literal, Optional, Union, overload

from housekeeping import deprecate_non_keyword_only_args

from reviewbot.deprecation import RemovedInReviewBot60Warning
from reviewbot.utils.log import get_logger


logger = get_logger(__name__)


@overload
def execute(
    command: Union[list[str], str],
    *,
    split_lines: Literal[False] = False,
    return_errors: Literal[False] = False,
    **kwargs,
) -> str:
    ...


@overload
def execute(
    command: Union[list[str], str],
    *,
    split_lines: Literal[True],
    return_errors: Literal[False] = False,
    **kwargs,
) -> list[str]:
    ...


@overload
def execute(
    command: Union[list[str], str],
    *,
    return_errors: Literal[True],
    split_lines: Literal[False] = False,
    none_on_ignored_error: Literal[False] = False,
    **kwargs,
) -> tuple[str, str]:
    ...


@overload
def execute(
    command: Union[list[str], str],
    *,
    split_lines: Literal[True] = True,
    return_errors: Literal[True] = True,
    none_on_ignored_error: Literal[False] = False,
    **kwargs,
) -> tuple[list[str], list[str]]:
    ...


@overload
def execute(
    command: Union[list[str], str],
    *,
    ignore_errors: Literal[True],
    return_errors: Literal[True],
    none_on_ignored_error: Literal[True],
    split_lines: Literal[False] = False,
    **kwargs,
) -> tuple[Optional[str], str]:
    ...


@overload
def execute(
    command: Union[list[str], str],
    *,
    split_lines: Literal[True],
    ignore_errors: Literal[True],
    return_errors: Literal[True],
    none_on_ignored_error: Literal[True],
    **kwargs,
) -> tuple[Optional[list[str]], list[str]]:
    ...


@deprecate_non_keyword_only_args(RemovedInReviewBot60Warning)
def execute(
    command: Union[list[str], str],
    *,
    env: Optional[dict[str, str]] = None,
    split_lines: bool = False,
    ignore_errors: bool = False,
    extra_ignore_errors: tuple[int, ...] = (),
    translate_newlines: bool = True,
    with_errors: bool = True,
    return_errors: bool = False,
    none_on_ignored_error: bool = False,
    **kwargs,
) -> Union[
        Union[str, list[str], None],
        tuple[Union[str, list[str], None], Union[str, list[str], None]],
    ]:
    r"""Execute a command and return the output.

    Version Changed:
        5.0:
        Arguments other than ``command`` are now keyword-only.

    Args:
        command (list of str):
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

        return_errors (bool, optional):
            Whether to return the content of the stderr stream. If set, this
            argument takes precedence over the ``with_errors`` argument.

        none_on_ignored_error (bool, optional):
            Whether to return ``None`` if there was an ignored error (instead
            of the process output).

        **kwargs (dict, unused):
            Additional keyword arguments, unused.

    Returns:
        object:
        This returns a single value or 2-tuple, depending on the arguments.

        If ``return_errors`` is ``True``, this will return the standard output
        and standard errors as strings in a tuple. Otherwise, this will just
        result the standard output as a string.

        If ``split_lines`` is ``True``, those strings will instead be lists
        of lines (preserving newlines).

        All resulting strings will be Unicode.
    """
    if isinstance(command, list):
        logger.debug(subprocess.list2cmdline(command))
    else:
        logger.debug(command)

    if env:
        env.update(os.environ)
    else:
        env = os.environ.copy()

    env['LC_ALL'] = 'en_US.UTF-8'
    env['LANGUAGE'] = 'en_US.UTF-8'

    if with_errors and not return_errors:
        errors_output = subprocess.STDOUT
    else:
        errors_output = subprocess.PIPE

    if sys.platform.startswith('win'):
        p = subprocess.Popen(command,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=errors_output,
                             shell=False,
                             text=translate_newlines,
                             env=env)
    else:
        p = subprocess.Popen(command,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=errors_output,
                             shell=False,
                             close_fds=True,
                             text=translate_newlines,
                             env=env)

    data, errors = p.communicate()

    if isinstance(data, bytes):
        data = data.decode('utf-8')

    if isinstance(errors, bytes):
        errors = errors.decode('utf-8')

    assert isinstance(data, str)
    assert errors is None or isinstance(errors, str)

    if split_lines:
        data = data.splitlines(True)

    if return_errors:
        if split_lines and errors is not None:
            errors = errors.splitlines(True)
    else:
        errors = None

    rc = p.wait()

    if rc and not ignore_errors and rc not in extra_ignore_errors:
        raise Exception(f'Failed to execute command: {command}\n{data}')

    if rc and none_on_ignored_error:
        data = None

    if return_errors:
        return data, errors
    else:
        return data


_is_exe_in_path_cache: dict[str, Optional[str]] = {}


def is_exe_in_path(
    name: str,
    cache: Optional[dict[str, Optional[str]]] = None,
) -> bool:
    """Check whether an executable is in the user's search path.

    If the provided filename is an absolute path, it will be checked
    directly without looking in the search path.

    Version Changed:
        3.0:
        Added the ``cache`` parameter.

    Args:
        name (str):
            The name of the executable, without any platform-specific
            executable extension. The extension will be appended if necessary.

        cache (dict, optional):
            A result cache, to avoid repeated lookups.

            This will store the paths to any files that are found (or ``None``
            if not found).

            By default, the cache is shared across all calls. A custom cache
            can be provided instead.

    Returns:
        bool:
        True if the executable can be found in the execution path.
    """
    if cache is None:
        cache = _is_exe_in_path_cache

    if sys.platform == 'win32' and not name.endswith('.exe'):
        name += '.exe'

    if name in cache:
        return cache[name] is not None

    path = None

    if os.path.isabs(name):
        if os.path.exists(name):
            path = name
    else:
        for dirname in os.environ['PATH'].split(os.pathsep):
            temp_path = os.path.abspath(os.path.join(dirname, name))

            if os.path.exists(temp_path):
                path = temp_path
                break

    cache[name] = path

    return (path is not None)
