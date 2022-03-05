"""Common exceptions for tools and processing."

Version Added:
    3.0
"""

from __future__ import unicode_literals


class SuspiciousFilePath(Exception):
    """A file referenced in a change is suspicious.

    This usually means the file had too many ``../`` components, as a means
    of potentially referencing outside its source tree.

    Version Added:
        3.0
    """

    def __init__(self, path):
        """Initialize the exception.

        Args:
            path (unicode):
                The path that was suspicious.
        """
        self.path = path
