"""Decorators for tool tests.

Version Added:
    3.0
"""

from __future__ import unicode_literals


def integration_test(**kwargs):
    """Decorate a unit test and mark it as an integration test.

    The arguments provided to this decorator will be passed to
    :py:meth:`~reviewbot.tools.testing.testcases.BaseToolTestCase
    .setup_integration_test`.

    Version Added:
        3.0

    Args:
        **kwargs (dict):
            Keyword arguments to pass during setup.

    Returns:
        callable:
        The new unit test function.
    """
    def _dec(func):
        func.integration_setup_kwargs = kwargs

        return func

    return _dec


def simulation_test(**kwargs):
    """Decorate a unit test and mark it as a simulation test.

    The arguments provided to this decorator will be passed to
    :py:meth:`~reviewbot.tools.testing.testcases.BaseToolTestCase
    .setup_simulation_test`.

    Version Added:
        3.0

    Args:
        **kwargs (dict):
            Keyword arguments to pass during setup.

    Returns:
        callable:
        The new unit test function.
    """
    def _dec(func):
        func.simulation_setup_kwargs = kwargs

        return func

    return _dec
