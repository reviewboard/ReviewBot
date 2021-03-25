"""Base support for code checking tools."""

from __future__ import unicode_literals

from reviewbot.deprecation import RemovedInReviewBot40Warning
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

    #: Internal state for marking this as a legacy tool.
    #:
    #: Do not change this. It is necessary for legacy tools to continue to
    #: work in Review Bot 3.0.
    #:
    #: Version Added:
    #:     3.0
    #:
    #: Type:
    #:     bool
    legacy_tool = True

    def __new__(cls, *args, **kwargs):
        """Create an instance of the tool.

        This will emit a deprecation warning, warning of impending removal
        and the changes that will be needed.

        Args:
            *args (tuple):
                Positional arguments to pass to the constructor.

            **kwargs (dict):
                Keyword arguments to pass to the constructor.

        Returns:
            Tool:
            A new instance of the tool.
        """
        RemovedInReviewBot40Warning.warn(
            '%s must subclass reviewbot.tools.base.BaseTool. All '
            'overridden methods, including __init__() and handle_file(), '
            'must take a **kwargs argument, and self.settings should be '
            'accessed for tool-specific settings. Legacy support will be '
            'removed in Review Bot 4.0.'
            % cls.__name__)

        return super(Tool, cls).__new__(cls)


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

    #: Internal state for marking this as a legacy tool.
    #:
    #: Do not change this. It is necessary for legacy tools to continue to
    #: work in Review Bot 3.0.
    #:
    #: Version Added:
    #:     3.0
    #:
    #: Type:
    #:     bool
    legacy_tool = True

    def __new__(cls, *args, **kwargs):
        """Create an instance of the tool.

        This will emit a deprecation warning, warning of impending removal
        and the changes that will be needed.

        Args:
            *args (tuple):
                Positional arguments to pass to the constructor.

            **kwargs (dict):
                Keyword arguments to pass to the constructor.

        Returns:
            Tool:
            A new instance of the tool.
        """
        RemovedInReviewBot40Warning.warn(
            '%s must subclass reviewbot.tools.base.BaseTool, and mix in '
            'reviewbot.tools.base.mixins.FullRepositoryToolMixin. All '
            'overridden methods, including __init__() and handle_file(), '
            'must take a **kwargs argument, and self.settings should be '
            'accessed for tool-specific settings. Legacy support will be '
            'removed in Review Bot 4.0.'
            % cls.__name__)

        return super(RepositoryTool, cls).__new__(cls)
