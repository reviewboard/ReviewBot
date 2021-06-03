"""Utility functions for working with text."""

from __future__ import unicode_literals

import re


_SPLIT_RE = re.compile(r'\s*,+\s*')


def split_comma_separated(s):
    """Return a list of values from a comma-separated string.

    Any blank values will be filtered out.

    Args:
        s (unicode):
            The string to split.

    Returns:
        list of unicode:
        The list of values.
    """
    return [
        item
        for item in _SPLIT_RE.split(s)
        if item
    ]
