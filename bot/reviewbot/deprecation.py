"""Internal support for handling deprecations in Review Bot.

The version-specific objects in this module are not considered stable between
releases, and may be removed at any point. The base objects are considered
stable.

Version Added:
    3.0
"""

from __future__ import annotations

import warnings
from typing import Final, final

from housekeeping import BaseRemovedInWarning


class BaseRemovedInReviewBotVersionWarning(BaseRemovedInWarning):
    """Base class for a Review Bot deprecation warning.

    All version-specific deprecation warnings inherit from this, allowing
    callers to check for Review Bot deprecations without being tied to a
    specific version.
    """

    product: Final[str] = 'Review Bot'


@final
class RemovedInReviewBot60Warning(BaseRemovedInReviewBotVersionWarning):
    """Deprecations for features removed in Review Bot 6.0.

    Note that this class will itself be removed in Review Bot 6.0. If you need
    to check against Review Bot deprecation warnings, please see
    :py:class:`BaseRemovedInReviewBotVersionWarning`. Alternatively, you can
    use the alias for this class,
    :py:data:`RemovedInNextReviewBotVersionWarning`.
    """

    version = '6.0'


#: An alias for the next release of Review Bot where features would be removed.
RemovedInNextReviewBotVersionWarning = RemovedInReviewBot60Warning


# Enable each warning for display.
for _warning_cls in [RemovedInReviewBot60Warning]:
    warnings.simplefilter('once', _warning_cls, 0)
