from __future__ import unicode_literals

import os
import tempfile


tempfiles = []


def cleanup_tempfiles():
    """Clean up all temporary files.

    This will delete all the files created by :py:func:`make_tempfile`.
    """
    global tempfiles

    for tmpfile in tempfiles:
        try:
            os.unlink(tmpfile)
        except:
            pass

    tempfiles = []


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
    fd, tmpfile = tempfile.mkstemp(suffix=extension)

    if content:
        os.write(fd, content)

    os.close(fd)
    tempfiles.append(tmpfile)
    return tmpfile
