"""API utility functions.

Version Added:
    3.0
"""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from rbtools.api.client import RBClient

from reviewbot import get_version_string
from reviewbot.config import config

if TYPE_CHECKING:
    from rbtools.api.resource import RootResource


def get_api_root(
    url: str,
    username: Optional[str] = None,
    api_token: Optional[str] = None,
    session: Optional[str] = None,
) -> RootResource:
    """Return the root of the Review Board API.

    Either ``session`` or both ``username`` and ``api_token`` must be
    provided.

    Version Added:
        3.0

    Args:
        url (str):
            The path to the Review Board server.

        username (str, optional):
            The username used for authentication.

        api_token (str, optional):
            The API token used for authentication.

        session (str, optional):
            An existing Review Board session identifier.

    Returns:
        rbtools.api.resources.RootResource:
        The root API resource for the server.

    Raises:
        rbtools.api.errors.APIError:
            There was an error fetching the root resource.
    """
    client = RBClient(url,
                      agent=f'ReviewBot/{get_version_string()}',
                      cookie_file=config['cookie_path'],
                      username=username,
                      api_token=api_token,
                      session=session)

    return client.get_root()
