from __future__ import unicode_literals

import logging
import os

import appdirs

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
        execute(['git', 'clone', '--local', '--depth', '1',
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


def init_repositories():
    """Set up configured repositories."""
    global repositories

    for repository in config['repositories']:
        repo_name = repository['name']
        repo_type = repository.get('type')

        if repo_type == 'git':
            repositories[repo_name] = \
                GitRepository(repo_name, repository['clone_path'])
        elif repo_type == 'hg':
            repositories[repo_name] = \
                HgRepository(repo_name, repository['clone_path'])
        else:
            logging.error('Unknown type "%s" for configured repository %s',
                          repo_type, repo_name)
