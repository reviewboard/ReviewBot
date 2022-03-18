"""Full access repository management."""

from __future__ import unicode_literals

import os
from uuid import uuid4

import appdirs
import six

from reviewbot.config import config
from reviewbot.utils.api import get_api_root
from reviewbot.utils.filesystem import make_tempdir
from reviewbot.utils.log import get_logger
from reviewbot.utils.process import execute


logger = get_logger(__name__)


repositories = {}
repository_backends = []


class BaseRepository(object):
    """A repository.

    Attributes:
        clone_path (unicode):
            The clone path of the repository. This may be the ``path`` or
            ``mirror_path`` of the repository in the API.

        name (unicode):
            The name of the repository.

        repo_path (unicode):
            The local path where the clone/checkout is or will be stored.
    """

    #: A tuple of known repository configuration types this supports.
    #:
    #: Version Added:
    #:     3.0
    #:
    #: Type:
    #:     tuple of unicode
    repo_types = None

    #: The Review Board tool name that this supports.
    #:
    #: Version Added:
    #:     3.0
    #:
    #: Type:
    #:     unicode
    tool_name = None

    def __init__(self, name, clone_path):
        """Initialize the repository.

        Args:
            name (unicode):
                The name of the repository.

            clone_path (unicode):
                The clone path of the repository.

            repo_path (unicode):
        """
        self.name = name
        self.clone_path = clone_path

        self.repo_path = os.path.join(appdirs.site_data_dir('reviewbot'),
                                      'repositories', name)

    def sync(self):
        """Sync the latest state of the repository."""
        raise NotImplementedError

    def checkout(self, commit_id):
        """Check out the given commit.

        Args:
            commit_id (unicode):
                The ID of the commit to check out.

        Returns:
            unicode:
            The name of a directory with the given checkout.
        """
        raise NotImplementedError

    def __eq__(self, other):
        """Return whether this repository is equal to another.

        Args:
            other (Repository):
                The repository to compare to.

        Returns:
            bool:
            ``True`` if the two repositories are equal. ``False`` if they are
            not.
        """
        return (type(self) is type(other) and
                self.name == other.name and
                self.clone_path == other.clone_path)

    def __repr__(self):
        """Return a string representation of the repository.

        Version Added:
            3.0

        Returns:
            unicode:
            A string representation.
        """
        return '<%s(name=%r, clone_path=%r, repo_path=%r)>' % (
            type(self).__name__, self.name, self.clone_path, self.repo_path)


class GitRepository(BaseRepository):
    """A git repository."""

    repo_types = ('git',)
    tool_name = 'Git'

    def sync(self):
        """Sync the latest state of the repository."""
        if not os.path.exists(self.repo_path):
            os.makedirs(self.repo_path)

            logger.info('Cloning repository %s to %s',
                        self.clone_path, self.repo_path)
            execute(['git', 'clone', '--bare', self.clone_path,
                     self.repo_path])
        else:
            logger.info('Fetching into existing repository %s',
                        self.repo_path)
            execute(['git', '--git-dir=%s' % self.repo_path, 'fetch',
                     'origin', '+refs/heads/*:refs/heads/*'])

    def checkout(self, commit_id):
        """Check out the given commit.

        Args:
            commit_id (unicode):
                The ID of the commit to check out.

        Returns:
            unicode:
            The name of a directory with the given checkout.
        """
        workdir = make_tempdir()
        branchname = 'br-%s-%s' % (commit_id, uuid4())

        logger.info('Creating temporary branch for clone in repo %s',
                    self.repo_path)
        execute(['git', '--git-dir=%s' % self.repo_path, 'branch', branchname,
                 commit_id])

        try:
            logger.info('Creating working tree for commit ID %s in %s', commit_id,
                        workdir)
            execute(['git', 'clone', '--local', '--no-hardlinks', '--depth', '1',
                     '--branch', branchname, self.repo_path, workdir])
        finally:
            logger.info('Removing temporary branch for clone in repo %s',
                        self.repo_path)
            execute(['git', '--git-dir=%s' % self.repo_path, 'branch', '-d',
                     branchname])

        return workdir


class HgRepository(BaseRepository):
    """A Mercurial repository."""

    repo_types = ('hg', 'mercurial')
    tool_name = 'Mercurial'

    def sync(self):
        """Sync the latest state of the repository."""
        if not os.path.exists(self.repo_path):
            os.makedirs(self.repo_path)

            logger.info('Cloning repository %s to %s',
                        self.clone_path, self.repo_path)
            execute(['hg', 'clone', '-U', self.clone_path,
                     self.repo_path])
        else:
            logger.info('Pulling into existing repository %s',
                        self.repo_path)
            execute(['hg', '-R', self.repo_path, 'pull'])

    def checkout(self, commit_id):
        """Check out the given commit.

        Args:
            commit_id (unicode):
                The ID of the commit to check out.

        Returns:
            unicode:
            The name of a directory with the given checkout.
        """
        workdir = make_tempdir()

        logger.info('Creating working tree for commit ID %s in %s', commit_id,
                    workdir)
        execute(['hg', '-R', self.repo_path, 'archive', '-r', commit_id,
                 '-t', 'files', workdir])

        return workdir


def fetch_repositories(url, user=None, token=None):
    """Fetch repositories from Review Board.

    Args:
        url (unicode):
            The configured url for the connection.

        user (unicode):
            The configured user for the connection.

        token (unicode):
            The configured API token for the user.
    """
    logger.info('Fetching repositories from Review Board: %s', url)

    root = get_api_root(url=url,
                        username=user,
                        api_token=token)

    for repository_cls in repository_backends:
        repos = root.get_repositories(tool=repository_cls.tool_name,
                                      only_links='',
                                      only_fields='path,mirror_path,name')

        for repo in repos.all_items:
            clone_path = None

            for path in (repo.path, repo.mirror_path):
                if (os.path.exists(path) or path.startswith('http') or
                    path.startswith('git')):
                    clone_path = path
                    break

            if clone_path:
                repositories[repo.name] = repository_cls(
                    name=repo.name,
                    clone_path=clone_path)
            else:
                logger.warning('Cannot find usable path for repository: %s',
                               repo.name)


def init_repositories():
    """Set up configured repositories.

    This will set up any configured Review Board servers and fetch any
    repositories specified in the configuration. As part of this, it will
    validate the configuration and skip any entries that are misconfigured
    or result in any unexpected errors.
    """
    global repository_backends

    repository_backends = [
        GitRepository,
        HgRepository,
    ]

    for server in config['reviewboard_servers']:
        if 'url' not in server:
            logger.error('The following server configuration is missing the '
                         '"url" key: %r',
                         server)
            continue

        server_kwargs = {
            'url': server['url'],
            'user': server.get('user'),
            'token': server.get('token'),
        }

        try:
            fetch_repositories(**server_kwargs)
        except Exception as e:
            logger.error('Unexpected error fetching repositories for '
                         'Review Board server configuration %r: %s',
                         server, e)

    for repository in config['repositories']:
        missing_keys = ({'name', 'type', 'clone_path'} -
                        set(six.iterkeys(repository)))

        if missing_keys:
            logger.error(
                'The following repository configuration is '
                'missing the %s key(s): %r',
                ', '.join(
                    '"%s"' % _key
                    for _key in sorted(missing_keys)
                ),
                repository)
            continue

        repo_name = repository['name']
        repo_type = repository['type']
        repo_kwargs = {
            'name': repo_name,
            'clone_path': repository['clone_path'],
        }

        for repository_cls in repository_backends:
            if repo_type in repository_cls.repo_types:
                try:
                    repositories[repo_name] = repository_cls(**repo_kwargs)
                except Exception as e:
                    logger.error('Unexpected error initializing repository '
                                 'for configuration %r: %s',
                                 repository, e)

                break
        else:
            logger.error('Unknown type "%s" for configured repository %s',
                         repo_type, repo_name)


def reset_repositories():
    """Reset the repository state.

    This is primarily intended for unit tests.

    Version Added:
        3.0
    """
    repositories.clear()
