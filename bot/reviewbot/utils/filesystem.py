"""Utilities for filesystem operations and path normalization."""

from __future__ import unicode_literals

import ntpath
import os
import posixpath
import shutil
import tempfile
from contextlib import contextmanager
from enum import Enum

from reviewbot.errors import SuspiciousFilePath
from reviewbot.utils.log import get_logger


logger = get_logger(__name__)


tmpdirs = []
tmpfiles = []


class PathPlatform(Enum):
    """The platform used to generate a filesystem path.

    Version Added:
        3.0
    """

    #: A DOS/Windows path.
    WINDOWS = 'win'

    #: A POSIX path.
    POSIX = 'posix'

    if os.path is posixpath:
        LOCAL = POSIX
    else:
        LOCAL = WINDOWS

    @property
    def path_mod(self):
        """The path module used to work with paths of this type.

        Returns:
            module:
            The path module (either :py:mod:`ntpath` or :py:mod:`posixpath`).
        """
        if self == self.POSIX:
            return posixpath
        else:
            assert self == self.WINDOWS
            return ntpath


@contextmanager
def chdir(path):
    """Temporarily change directory into the given working directory.

    Args:
        path (unicode):
            The directory to operate within.
    """
    cwd = os.getcwd()

    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(cwd)


def cleanup_tempfiles():
    """Clean up all temporary files.

    This will delete all the files created by :py:func:`make_tempfile`.
    """
    global tmpdirs
    global tmpfiles

    for tmpdir in tmpdirs:
        try:
            logger.debug('Removing temporary directory %s', tmpdir)
            shutil.rmtree(tmpdir)
        except:
            pass

    for tmpfile in tmpfiles:
        try:
            logger.debug('Removing temporary file %s', tmpfile)
            os.unlink(tmpfile)
        except:
            pass

    tmpdirs[:] = []
    tmpfiles[:] = []


def make_tempfile(content=None, extension=''):
    """Create a temporary file and return the path.

    Args:
        content (bytes, optional):
            Optional content to put in the file.

        extension (unicode, optional):
            An optional file extension to add to the end of the filename.

    Returns:
        unicode:
        The name of the new file.
    """
    global tmpfiles
    fd, tmpfile = tempfile.mkstemp(suffix=extension)

    if content:
        os.write(fd, content)

    os.close(fd)
    tmpfiles.append(tmpfile)
    return tmpfile


def make_tempdir():
    """Create a temporary directory and return the path.

    Returns:
        unicode:
        The name of the new directory.
    """
    global tmpdirs

    tmpdir = tempfile.mkdtemp()
    tmpdirs.append(tmpdir)
    return tmpdir


def ensure_dirs_exist(path):
    """Ensure directories exist to an absolute path.

    Args:
        path (unicode):
            The absolute path for which directories should be created if they
            don't exist.

    Raises:
        ValueError:
            If the path is not absolute.

        OSError:
            If making the directory failed.
    """
    if not os.path.isabs(path):
        raise ValueError

    folder_path = os.path.dirname(path)

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)


def get_path_platform(path):
    """Return the platform most likely used to generate a path.

    This supports Windows and POSIX filesystem and UNC paths.

    Version Added:
        3.0

    Args:
        path (unicode):
            The Windows or POSIX path.

    Returns:
        PathPlatform:
        The platform that the path is most likely for.
    """
    nt_drive, nt_path = ntpath.splitdrive(path)

    if nt_drive:
        if nt_drive.startswith('//'):
            # This is a POSIX-style UNC path.
            return PathPlatform.POSIX
        else:
            # There's a drive letter, so this is probably a Windows path.
            return PathPlatform.WINDOWS

    # No drive letter, so let's look at the path and try to determine from
    # there.
    posix_parts = path.split(posixpath.sep)

    if len(posix_parts) > 1:
        # Windows doesn't allow "/" in filenames, though it might be used as
        # a path separator. In either case, we can treat this as POSIX.
        return PathPlatform.POSIX

    nt_parts = path.split(ntpath.sep)

    if len(nt_parts) > 1:
        # This is probably a Windows path, then. It could be a POSIX path
        # with backslashes in the filenames, which means we might get this
        # wrong, but that's probably far less common.
        return PathPlatform.WINDOWS

    # It's a bare path with no directories. Treat it as POSIX.
    return PathPlatform.POSIX


def normalize_platform_path(path, relative_to=None,
                            target_platform=PathPlatform.LOCAL):
    """Normalize a path from a diff, making it suitable for local use.

    This will convert either a Windows or POSIX path to the local platform,
    collapsing any relative components (such as ``..``) within, and then
    making the result relative.

    The path can optionally be joined to a path specified in ``relative_to``.

    Version Added:
        3.0

    Args:
        path (unicode):
            The path to normalize.

        relative_to (unicode, optional):
            An optional directory that the normalized path should be joined
            to.

        target_platform (PathPlatform, optional):
            The target platform for the normalized path. This is mostly
            for unit testing purposes.

    Returns:
        unicode:
        The resulting normalized path.

    Raises:
        reviewbot.errors.SuspiciousFilePath:
            The resulting normalized file path is suspicious. It would have
            resulted in access outside the source tree.
    """
    path_platform = get_path_platform(path)
    path_mod = path_platform.path_mod
    target_path_mod = target_platform.path_mod

    norm_path = path
    is_abs = path_mod.isabs(norm_path)

    if (is_abs and
        (path_platform == PathPlatform.WINDOWS or
         norm_path.startswith('//'))):
        # This is an absolute path, or a UNC path. posixpath.splitdrive()
        # won't handle UNC paths, but ntpath.splitdrive() will (and handle
        # either / or \ delimeters.
        norm_path = ntpath.splitdrive(norm_path)[1]

    # Convert the path delimiter.
    norm_path = path_mod.normpath(norm_path)
    path_parts = norm_path.split(path_mod.sep)

    if is_abs:
        # Get rid of the bit that makes this an absolute path.
        path_parts = path_parts[1:]

    if path_parts[0] == '..':
        # normpath wasn't good enough. The path tried to escape!
        raise SuspiciousFilePath(path)

    norm_path = target_path_mod.join(*path_parts)

    # Make sure things still look sane.
    assert not target_path_mod.isabs(norm_path)
    assert target_path_mod.normpath(norm_path) == norm_path

    if relative_to:
        norm_path = target_path_mod.join(relative_to, norm_path)

    return norm_path
