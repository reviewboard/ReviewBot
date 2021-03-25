"""Base support for code checking tools."""

from __future__ import unicode_literals

from reviewbot.tools.base import BaseTool, FullRepositoryToolMixin


class Tool(BaseTool):
    """Legacy base class for tools.

    Deprecated:
        3.0:
        Subclasses should instead inherit from
        :py:class:`reviewbot.tools.base.tool.BaseTool` (or a more specific
        subclass).

        This will be removed in Review Bot 4.0.
    """


class RepositoryTool(FullRepositoryToolMixin, BaseTool):
    """Legacy base class for tools that need access to the entire repository.

    Deprecated:
        3.0:
        Subclasses should instead inherit from
        :py:class:`reviewbot.tools.base.tool.BaseTool` (or a more specific
        subclass) and mix in
        :py:class:`reviewbot.tools.base.mixins.FullRepositoryToolMixin`.

        This will be removed in Review Bot 4.0.
    """
