"""Compatibility logging code for modern versions of Review Board.

Version Added:
    4.0.1
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from djblets.log import (TimedLogInfo as DjbletsTimedLogInfo,
                         log_timed as djblets_log_timed)

if TYPE_CHECKING or hasattr(DjbletsTimedLogInfo, '__enter__'):
    TimedLogInfo = DjbletsTimedLogInfo
    log_timed = djblets_log_timed
else:
    import logging
    from datetime import datetime, timezone
    from typing import Literal, Mapping, Optional
    from uuid import uuid4

    if TYPE_CHECKING:
        from django.http import HttpRequest

    class TimedLogInfo(DjbletsTimedLogInfo):
        """Tracks the time between operations for logging purposes.

        This is created and returned by :py:func:`log_timed` to track how long
        an operation takes, warning or critical-erroring if it takes too long.

        This class is a backport compatibility class for
        :py:class:`djblets.log.TimedLogInfo`. It will be removed when
        Djblets 5.3 is the minimum version required for Integrations.

        Version Added:
            4.0.1
        """

        ######################
        # Instance variables #
        ######################

        #: Extra information to include with all log items.
        #:
        #: This will be populated with ``request``.
        #:
        #: Version Added:
        #:     5.3
        extra: Mapping[str, object]

        #: The logger used for all log entries.
        #:
        #: Version Added:
        #:     5.3
        logger: logging.Logger

        #: The trace ID to include in log messages.
        #:
        #: This is used to help follow the chain of events in a series of logs.
        #:
        #: Version Added:
        #:     5.3
        trace_id: str

        def __init__(
            self,
            *,
            message: str,
            warning_at: float,
            critical_at: float,
            default_level: int,
            log_beginning: bool,
            request: Optional[HttpRequest],
            extra: Mapping[str, object] = {},
            logger: Optional[logging.Logger] = None,
            trace_id: Optional[str] = None,
        ) -> None:
            """Initialize the state for the timer.

            Args:
                message (str):
                    The message to show for the log entries.,

                warning_at (float):
                    The number of seconds at which to log warnings.

                    This may contain fractions of seconds.

                critical_at (float):
                    The number of seconds at which to log critical errors.

                    This may contain fractions of seconds.

                default_level (int):
                    The default log level for the timing information.

                log_beginning (bool):
                    Whether to log the beginning time for the operation.

                request (django.http.HttpRequest, optional):
                    The optional HTTP request associated with the operation.

                extra (dict, optional):
                    Extra information to include with all log items.

                    This will be populated with ``request`` and ``trace_id``.

                logger (logging.Logger, optional):
                    The logger used for all log entries.

                trace_id (str, optional):
                    The trace ID to include in log messages.

                    This is used to help follow the chain of events in a
                    series of logs.
            """
            self.message = message
            self.warning_at = warning_at
            self.critical_at = critical_at
            self.default_level = default_level
            self.start_time = datetime.now(timezone.utc)
            self.request = request

            if logger is None:
                logger = logging.getLogger()

            if not trace_id:
                trace_id = str(uuid4())

            extra = {
                **extra,
                'request': self.request,
                'trace_id': trace_id,
            }

            self.extra = extra
            self.logger = logger
            self.trace_id = trace_id

            if log_beginning:
                logger.log(default_level,
                           f'[%s] Begin: {message}',
                           trace_id,
                           extra=extra)

        def __enter__(self) -> TimedLogInfo:
            """Enter the context for the timer.

            This will open the context and return itself, allowing the timer
            to automatically complete when the context ends.

            Context:
                TimedLogInfo:
                This object.
            """
            return self

        def __exit__(self, *args, **kwargs) -> Literal[False]:
            """Exit the context for the timer.

            This will log the end time of the operation, stopping the timer.

            Args:
                *args (tuple, unused):
                    Unused positional arguments.

                **kwargs (dict, unused):
                    Unused keyword arguments.
            """
            self.done()

            return False

        def done(self) -> None:
            """Stop the timed logging operation.

            The resulting time of the operation will be written to the log
            file.  The log level depends on how long the operation takes.
            """
            delta = datetime.now(timezone.utc) - self.start_time
            level = self.default_level
            logger = self.logger
            message = self.message
            extra = self.extra
            trace_id = self.trace_id
            total_seconds = delta.total_seconds()

            if total_seconds >= self.critical_at:
                level = logging.CRITICAL
            elif total_seconds >= self.warning_at:
                level = logging.WARNING

            logger.log(self.default_level,
                       f'[%s] End: {message}',
                       trace_id,
                       extra=extra)
            logger.log(level,
                       f'[%s] {message} took %d.%06d seconds',
                       trace_id,
                       delta.seconds,
                       delta.microseconds,
                       extra=extra)

    def log_timed(
        message: str,
        *,
        warning_at: float = 5,
        critical_at: float = 15,
        log_beginning: bool = True,
        default_level: int = logging.DEBUG,
        request: Optional[HttpRequest] = None,
        extra: Mapping[str, object] = {},
        logger: Optional[logging.Logger] = None,
        trace_id: Optional[str] = None,
    ) -> TimedLogInfo:
        """Times an operation, logging timing information.

        This will display a log message at the start of an operation and at the
        end, displaying the time taken for the operation. The final log entry's
        level will depend on the amount of time taken, switching to a warning
        if at ``warning_at`` seconds and a critical error at ``critical_at``
        seconds.

        This function can be called directly or used as a context manager.

        This class is a backport compatibility class for
        :py:class:`djblets.log.TimedLogInfo`. It will be removed when
        Djblets 5.3 is the minimum version required for Integrations.

        Version Added:
            4.0.1

        Args:
            message (str):
                The message to show for the log entries.,

            warning_at (int):
                The number of seconds at which to log warnings.

                This may contain fractions of seconds.

            critical_at (int):
                The number of seconds at which to log critical errors.

                This may contain fractions of seconds.

            default_level (int):
                The default log level for the timing information.

            log_beginning (bool):
                Whether to log the beginning time for the operation.

            request (django.http.HttpRequest, optional):
                The optional HTTP request associated with the operation.

            extra (dict, optional):
                Extra information to include with all log items.

                This will be populated with ``request`` and ``trace_id``.

            logger (logging.Logger, optional):
                The logger used for all log entries.

            trace_id (str, optional):
                The trace ID to include in log messages.

                This is used to help follow the chain of events in a series of
                logs.

                If not provided, one will be generated. This can then be
                accessed on :py:attr:`TimedLogInfo.trace_id`.

        Example:
            .. code-block:: python

               from djblets.log import log_timed

               # As a direct function call:
               t = log_timed('Doing a thing')

               try:
                   ...
               finally:
                   t.done()

               # As a context manager:
               with log_timed('Doing a thing') as t:
                   ...
        """
        return TimedLogInfo(message=message,
                            warning_at=warning_at,
                            critical_at=critical_at,
                            default_level=default_level,
                            log_beginning=log_beginning,
                            request=request,
                            extra=extra,
                            logger=logger,
                            trace_id=trace_id)
