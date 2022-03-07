"""Utility functions for loggers.

Version Added:
    3.0
"""

from __future__ import unicode_literals

from celery.utils.log import (get_logger as _get_logger,
                              get_task_logger as _get_task_logger)


def get_logger(name, is_task_logger=True):
    """Return a logger with the given name.

    The logger will by default be constructed as a task logger. This will
    ensure it contains additional information on the current task name and task
    ID, if running in a task. If executed outside of a task, the name name and
    ID will be replaced with ``???`` by Celery.

    Task logging should be turned off only when we know for sure that the
    code isn't going to be running in a task.

    Version Added:
        3.0

    Args:
        name (unicode):
            The name shown in the log line. This is expected to be a module
            name.

        is_task_logger (bool, optional):
            Whether to construct a task logger.

    Returns:
        logging.Logger:
        The new (or existing) logger for the given name.
    """
    if is_task_logger:
        return _get_task_logger(name)

    return _get_logger(name)


def get_root_logger():
    """Return a root logger for Review Bot.

    This will use "Review Bot" as the logger name.

    Version Added:
        3.0

    Returns:
        logging.Logger:
        The root logger.
    """
    return get_logger('Review Bot', is_task_logger=False)
