"""Base support for code checking tools.

This module provides convenient imports for specific base classes:

* :py:class:`~reviewbot.tools.base.BaseTool`

Version Added:
    3.0
"""

from __future__ import unicode_literals

from reviewbot.tools.base.tool import BaseTool
from reviewbot.tools.base.mixins import (FilePatternsFromSettingMixin,
                                         FullRepositoryToolMixin,
                                         JavaToolMixin)


__all__ = [
    'BaseTool',
    'FilePatternsFromSettingMixin',
    'FullRepositoryToolMixin',
    'JavaToolMixin',
]
