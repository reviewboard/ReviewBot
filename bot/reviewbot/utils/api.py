"""API utility functions.

Version Added:
    3.0
"""

from __future__ import unicode_literals

from rbtools.api.client import RBClient

from reviewbot import get_version_string
from reviewbot.config import config


def get_api_root(url, username=None, api_token=None, session=None):
    """Return the root of the Review Board API.

    Either ``session`` or both ``username`` and ``api_token`` must be
    provided.

    Version Added:
        3.0

    Args:
        url (unicode):
            The path to the Review Board server.

        username (unicode, optional):
            The username used for authentication.

        api_token (unicode, optional):
            The API token used for authentication.

        session (unicode, optional):
            An existing Review Board session identifier.

    Returns:
        rbtools.api.resources.RootResource:
        The root API resource for the server.

    Raises:
        rbtools.api.errors.APIError:
            There was an error fetching the root resource.
    """
    client = RBClient(url,
                      agent='ReviewBot/%s' % get_version_string(),
                      cookie_file=config['cookie_path'],
                      username=username,
                      api_token=api_token,
                      session=session)

    return client.get_root()
