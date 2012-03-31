import os
import tempfile

tempfiles = []


def cleanup_tempfiles():
    global tempfiles
    for tmpfile in tempfiles:
        try:
            os.unlink(tmpfile)
        except:
            pass
    tempfiles = []


def make_tempfile(content=None):
    """
    Creates a temporary file and returns the path. The path is stored
    in an array for later cleanup.
    """
    fd, tmpfile = tempfile.mkstemp()

    if content:
        os.write(fd, content)

    os.close(fd)
    tempfiles.append(tmpfile)
    return tmpfile
