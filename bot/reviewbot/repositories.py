from __future__ import unicode_literals

import logging
import os

import appdirs

from rbtools.api.client import RBClient

from reviewbot.config import config
from reviewbot.utils.filesystem import make_tempdir
from reviewbot.utils.process import execute


repositories = {}


class Repository(object):
    """A repository."""

    def sync(self):
        """Sync the latest state of the repository."""
        pass


class GitRepository(Repository):
    """A git repository."""

    def __init__(self, name, clone_path):
        """Initialize the repository.

        Args:
            name (unicode):
                The configured name of the repository.

            clone_path (unicode):
                The path of the git remote to clone.
        """
        self.name = name
        self.clone_path = clone_path
        self.repo_path = os.path.join(appdirs.site_data_dir('reviewbot'),
                                      'repositories', name)

    def sync(self):
        """Sync the latest state of the repository."""
        if not os.path.exists(self.repo_path):
            os.makedirs(self.repo_path)

            logging.info('Cloning repository %s to %s',
                         self.clone_path, self.repo_path)
            execute(['git', 'clone', '--bare', self.clone_path,
                     self.repo_path])
        else:
            logging.info('Fetching into existing repository %s',
                         self.repo_path)
            execute(['git', '--git-dir=%s' % self.repo_path, 'fetch',
                     'origin', '+refs/heads/*:refs/heads/*', '--prune'])

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
        branchname = 'br-%s' % commit_id

        logging.info('Creating temporary branch for clone in repo %s',
                     self.repo_path)
        execute(['git', '--git-dir=%s' % self.repo_path, 'branch', branchname,
                 commit_id])

        logging.info('Creating working tree for commit ID %s in %s', commit_id,
                     workdir)
        execute(['git', 'clone', '--local', '--no-hardlinks', '--depth', '1',
                 '--branch', branchname, self.repo_path, workdir])

        logging.info('Removing temporary branch for clone in repo %s',
                     self.repo_path)
        execute(['git', '--git-dir=%s' % self.repo_path, 'branch', '-d',
                 branchname])

        return workdir


class HgRepository(Repository):
    """A hg repository."""

    def __init__(self, name, clone_path):
        """Initialize the repository.

        Args:
            name (unicode):
                The configured name of the repository.

            clone_path (unicode):
                The path of the hg repository to clone.
        """
        self.name = name
        self.clone_path = clone_path
        self.repo_path = os.path.join(appdirs.site_data_dir('reviewbot'),
                                      'repositories', name)

    def sync(self):
        """Sync the latest state of the repository."""
        if not os.path.exists(self.repo_path):
            os.makedirs(self.repo_path)

            logging.info('Cloning repository %s to %s',
                         self.clone_path, self.repo_path)
            execute(['hg', 'clone', '-U', self.clone_path,
                     self.repo_path])
        else:
            logging.info('Pulling into existing repository %s',
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

        logging.info('Creating working tree for commit ID %s in %s', commit_id,
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
    logging.info('Fetching repositories from Review Board: %s', url)
    # TODO: merge with COOKIE_FILE/AGENT in tasks.py
    root = RBClient(url, username=user, api_token=token,
                    cookie_file='reviewbot-cookies.txt',
                    agent='ReviewBot').get_root()

    for tool_type in ('Mercurial', 'Git'):
        repos = root.get_repositories(tool=tool_type, only_links='',
                                      only_fields='path,mirror_path,name')

        for repo in repos.all_items:
            repo_source = None

            for path in (repo.path, repo.mirror_path):
                if (os.path.exists(path) or path.startswith('http') or
                    path.startswith('git')):
                    repo_source = path
                    break

            if repo_source:
                init_repository(repo.name, tool_type.lower(), repo_source)
            else:
                logging.warn('Cannot find usable path for repository: %s',
                             repo.name)


def init_repository(repo_name, repo_type, repo_source):
    """Add repository entry to global list.

    Args:
        repo_name (unicode):
            The name of the repository.

        repo_type (unicode):
            The type of the repository.

        repo_source (unicode):
            The source of the repository.
    """
    global repositories

    if repo_type == 'git':
        repositories[repo_name] = \
            GitRepository(repo_name, repo_source)
    elif repo_type in ('hg', 'mercurial'):
        repositories[repo_name] = \
            HgRepository(repo_name, repo_source)
    else:
        logging.error('Unknown type "%s" for configured repository %s',
                      repo_type, repo_name)


def init_repositories():
    """Set up configured repositories."""
    for server in config['review_board_servers']:
        fetch_repositories(server['url'],
                           server.get('user'),
                           server.get('token'))

    for repository in config['repositories']:
        repo_name = repository['name']
        repo_type = repository.get('type')
        repo_source = repository['clone_path']
        init_repository(repo_name, repo_type, repo_source)
