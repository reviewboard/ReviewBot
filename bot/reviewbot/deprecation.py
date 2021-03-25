"""Internal support for handling deprecations in Review Bot.

The version-specific objects in this module are not considered stable between
releases, and may be removed at any point. The base objects are considered
stable.

Version Added:
    3.0
"""

from __future__ import unicode_literals

import warnings


class BaseRemovedInReviewBotVersionWarning(DeprecationWarning):
    """Base class for a Review Bot deprecation warning.

    All version-specific deprecation warnings inherit from this, allowing
    callers to check for Review Bot deprecations without being tied to a
    specific version.
    """

    @classmethod
    def warn(cls, message, stacklevel=2):
        """Emit the deprecation warning.

        This is a convenience function that emits a deprecation warning using
        this class, with a suitable default stack level. Callers can provide
        a useful message and a custom stack level.

        Args:
            message (unicode):
                The message to show in the deprecation warning.

            stacklevel (int, optional):
                The stack level for the warning.
        """
        warnings.warn(message, cls, stacklevel=stacklevel + 1)


class RemovedInReviewBot40Warning(BaseRemovedInReviewBotVersionWarning):
    """Deprecations for features removed in Review Bot 4.0.

    Note that this class will itself be removed in Review Bot 4.0. If you need
    to check against Review Bot deprecation warnings, please see
    :py:class:`BaseRemovedInReviewBotVersionWarning`.
    """


class RemovedInReviewBot50Warning(BaseRemovedInReviewBotVersionWarning):
    """Deprecations for features removed in Review Bot 5.0.

    Note that this class will itself be removed in Review Bot 5.0. If you need
    to check against Review Bot deprecation warnings, please see
    :py:class:`BaseRemovedInReviewBotVersionWarning`. Alternatively, you can
    use the alias for this class,
    :py:data:`RemovedInNextReviewBotVersionWarning`.
    """


#: An alias for the next release of Review Bot where features would be removed.
RemovedInNextReviewBotVersionWarning = RemovedInReviewBot40Warning


# Enable each warning for display.
for _warning_cls in (RemovedInReviewBot40Warning, RemovedInReviewBot50Warning):
    warnings.simplefilter('once', _warning_cls, 0)
