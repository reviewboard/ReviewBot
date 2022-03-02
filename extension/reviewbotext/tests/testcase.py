"""Base support for Review Bot extension unit tests.

Version Added:
    3.0
"""

from __future__ import unicode_literals

from reviewboard.extensions.testing import ExtensionTestCase

from reviewbotext.extension import ReviewBotExtension


class TestCase(ExtensionTestCase):
    """Base class for Review Bot extension tests.

    Version Added:
        3.0
    """

    extension_class = ReviewBotExtension
