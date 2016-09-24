import os
import sys


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
        name += ".exe"

    for dir in os.environ['PATH'].split(os.pathsep):
        if os.path.exists(os.path.join(dir, name)):
            return True

    return False
