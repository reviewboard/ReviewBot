"""Utility functions for working with text."""

from __future__ import division, unicode_literals

import re


_BASE62_CHARS = \
    '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
_SPLIT_RE = re.compile(r'\s*,+\s*')


def base62_encode(value):
    """Return a base62-encoded string representing a numeric value.

    Args:
        value (int):
            The number to encode. This must be a positive number.

    Returns:
        bytes:
        The base62-encoded string.
    """
    if value == 0:
        return b'0'

    assert value > 0

    encoded = []

    while value > 0:
        value, remainder = divmod(value, 62)
        encoded.append(_BASE62_CHARS[remainder])

    encoded.reverse()

    return ''.join(encoded).encode('ascii')


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
