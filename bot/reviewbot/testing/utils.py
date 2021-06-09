"""Utility functions for unit tests.

Version Added:
    3.0
"""

from __future__ import unicode_literals

import os

import reviewbot


def get_test_dep_path(filename):
    """Return the path to a unit test dependency.

    This will be a path inside the :file:`tests/deps/` directory in the
    tree.

    Version Added:
        3.0

    Args:
        filename (unicode):
            The name of the file relative to the directory.

    Returns:
        unicode:
        The path to the dependency file.
    """
    return os.path.abspath(os.path.join(reviewbot.__file__, '..', '..',
                                        'tests', 'deps', filename))
