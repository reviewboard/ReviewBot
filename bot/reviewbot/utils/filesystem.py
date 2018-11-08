from __future__ import unicode_literals

import logging
import os
import shutil
import tempfile
from contextlib import contextmanager


tmpdirs = []
tmpfiles = []


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
            logging.debug('Removing temporary directory %s', tmpdir)
            shutil.rmtree(tmpdir)
        except:
            pass

    for tmpfile in tmpfiles:
        try:
            logging.debug('Removing temporary file %s', tmpfile)
            os.unlink(tmpfile)
        except:
            pass

    tmpdirs = []
    tmpfiles = []


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
