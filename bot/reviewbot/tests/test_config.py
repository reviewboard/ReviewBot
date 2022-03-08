"""Unit tests for reviewbot.config."""

from __future__ import unicode_literals

import json
import os
import shutil
import tempfile

import appdirs
import kgb

from reviewbot.config import config, logger, load_config
from reviewbot.testing import TestCase


class ConfigTests(kgb.SpyAgency, TestCase):
    """Unit tests for reviewbot.config."""

    def setUp(self):
        super(ConfigTests, self).setUp()

        self.spy_on(logger.info)
        self.spy_on(logger.error)
        self.spy_on(logger.warning)

    def test_load_config_with_env(self):
        """Testing load_config with $REVIEWBOT_CONFIG_FILE environment
        variable
        """
        fd, config_file = tempfile.mkstemp()

        with os.fdopen(fd, 'w') as fp:
            fp.write(
                'reviewboard_servers = [{\n'
                '    "url": "https://reviews.example.com/",\n'
                '}]\n'
                'repositories = [{\n'
                '    "name": "test",\n'
                '    "clone_path": "git@example.com:/repo.git",\n'
                '}]\n'
            )

        os.environ[str('REVIEWBOT_CONFIG_FILE')] = str(config_file)

        try:
            load_config()
        finally:
            del os.environ[str('REVIEWBOT_CONFIG_FILE')]

        self.assertEqual(config['reviewboard_servers'], [
            {
                'url': 'https://reviews.example.com/',
            },
        ])

        self.assertEqual(config['repositories'], [
            {
                'name': 'test',
                'clone_path': 'git@example.com:/repo.git',
            },
        ])

        self.assertSpyCalledWith(
            logger.info,
            'Loading Review Bot configuration file %s',
            config_file)
        self.assertSpyNotCalled(logger.warning)
        self.assertSpyNotCalled(logger.error)

    def test_load_config_with_default_path(self):
        """Testing load_config with default configuration file path"""
        config_file = self._load_custom_config(
            'reviewboard_servers = [{\n'
            '    "url": "https://reviews2.example.com/",\n'
            '}]\n'
            'repositories = [{\n'
            '    "name": "test",\n'
            '    "clone_path": "git@example.com:/repo2.git",\n'
            '}]\n'
        )

        self.assertEqual(config['reviewboard_servers'], [
            {
                'url': 'https://reviews2.example.com/',
            },
        ])
        self.assertEqual(config['repositories'], [
            {
                'name': 'test',
                'clone_path': 'git@example.com:/repo2.git',
            },
        ])

        self.assertSpyCalledWith(
            logger.info,
            'Loading Review Bot configuration file %s',
            config_file)
        self.assertSpyNotCalled(logger.warning)
        self.assertSpyNotCalled(logger.error)

    def test_load_config_with_not_found(self):
        """Testing load_config with configuration file not found"""
        tempdir = tempfile.mkdtemp()

        try:
            self.spy_on(appdirs.site_config_dir,
                        op=kgb.SpyOpReturn(tempdir))

            load_config()
        finally:
            os.rmdir(tempdir)

        self.assertEqual(config['reviewboard_servers'], [])
        self.assertEqual(config['repositories'], [])

        self.assertSpyCalledWith(
            logger.warning,
            'Configuration was not found at %s. Using the defaults.',
            os.path.join(tempdir, 'config.py'))

        self.assertSpyNotCalled(logger.info)
        self.assertSpyNotCalled(logger.error)

    def test_load_config_with_io_error(self):
        """Testing load_config with IOError reading file"""
        tempdir = tempfile.mkdtemp()

        try:
            os.mkdir(os.path.join(tempdir, 'config.py'), 0o755)
            self.spy_on(appdirs.site_config_dir,
                        op=kgb.SpyOpReturn(tempdir))

            load_config()
        finally:
            shutil.rmtree(tempdir)

        self.assertEqual(config['reviewboard_servers'], [])
        self.assertEqual(config['repositories'], [])

        self.assertSpyCalledWith(
            logger.info,
            'Loading Review Bot configuration file %s',
            os.path.join(tempdir, 'config.py'))
        self.assertSpyCalledWith(
            logger.error,
            'Unable to read the Review Bot configuration file: %s')
        self.assertSpyNotCalled(logger.warning)

    def test_load_config_with_deprecated_checkstyle_path(self):
        """Testing load_config with deprecated checkstyle_path setting"""
        config_file = self._load_custom_config(
            'checkstyle_path = "/path/to/checkstyle.jar"\n')

        self.assertNotIn('checkstyle_path', config)
        self.assertEqual(
            config['java_classpaths'],
            {
                'checkstyle': ['/path/to/checkstyle.jar'],
            })

        self.assertSpyCalledWith(
            logger.info,
            'Loading Review Bot configuration file %s',
            config_file)
        self.assertSpyCalledWith(
            logger.warning,
            'checkstyle_path in %s is deprecated and will be removed in '
            'Review Bot 4.0. Please put this in "java_classpaths". For '
            'example:\n'
            'java_classpaths = {\n'
            '    "checkstyle": ["%s"],\n'
            '}',
            config_file,
            '/path/to/checkstyle.jar')
        self.assertSpyNotCalled(logger.error)

    def test_load_config_with_deprecated_pmd_path(self):
        """Testing load_config with deprecated pmd_path setting"""
        config_file = self._load_custom_config('pmd_path = "/path/to/pmd"\n')

        self.assertNotIn('pmd_path', config)
        self.assertIn('exe_paths', config)
        self.assertIn('pmd', config['exe_paths'])
        self.assertEqual(config['exe_paths']['pmd'], '/path/to/pmd')

        self.assertSpyCalledWith(
            logger.info,
            'Loading Review Bot configuration file %s',
            config_file)
        self.assertSpyCalledWith(
            logger.warning,
            'pmd_path in %s is deprecated and will be '
            'removed in Review Bot 4.0. Please put '
            'this in "exe_paths". For example:\n'
            'exe_paths = {\n'
            '    "pmd": "%s",\n'
            '}',
            config_file,
            '/path/to/pmd')
        self.assertSpyNotCalled(logger.error)

    def test_load_config_with_deprecated_review_board_servers(self):
        """Testing load_config with deprecated review_board_servers setting"""
        config_file = self._load_custom_config(
            'review_board_servers = [{\n'
            '    "url": "https://reviews2.example.com/",\n'
            '}]\n'
            'repositories = [{\n'
            '    "name": "test",\n'
            '    "clone_path": "git@example.com:/repo2.git",\n'
            '}]\n'
        )

        self.assertIn('reviewboard_servers', config)
        self.assertNotIn('review_board_servers', config)
        self.assertEqual(config['reviewboard_servers'], [
            {
                'url': 'https://reviews2.example.com/',
            },
        ])

        self.assertSpyCalledWith(
            logger.info,
            'Loading Review Bot configuration file %s',
            config_file)
        self.assertSpyCalledWith(
            logger.warning,
            'review_board_servers in %s is deprecated and will be removed '
            'in Review Bot 4.0. Please rename it to reviewboard_servers or '
            'set reviewboard_servers_config_path to the location of a JSON '
            'file.',
            config_file)
        self.assertSpyNotCalled(logger.error)

    def test_load_config_with_default_cookie_dir(self):
        """Testing load_config with default cookie_dir setting"""
        self._load_custom_config('')

        cookie_dir = config['cookie_dir']
        default_cookie_dir = appdirs.user_cache_dir(appname='reviewbot',
                                                    appauthor='Beanbag')

        self.assertEqual(cookie_dir, default_cookie_dir)
        self.assertEqual(config['cookie_path'],
                         os.path.join(cookie_dir, 'reviewbot-cookies.txt'))

        self.assertSpyNotCalled(logger.error)

    def test_load_config_with_custom_cookie_dir(self):
        """Testing load_config with default cookie_dir setting"""
        new_cookie_dir = tempfile.mkdtemp()

        try:
            self._load_custom_config('cookie_dir = "%s"' % new_cookie_dir)
        finally:
            os.rmdir(new_cookie_dir)

        cookie_dir = config['cookie_dir']

        self.assertEqual(cookie_dir, new_cookie_dir)
        self.assertEqual(config['cookie_path'],
                         os.path.join(cookie_dir, 'reviewbot-cookies.txt'))

        self.assertSpyNotCalled(logger.error)

    def test_load_config_with_blank_cookie_dir(self):
        """Testing load_config with blank cookie_dir setting"""
        config_file = self._load_custom_config('cookie_dir = ""\n')

        cookie_dir = config['cookie_dir']
        default_cookie_dir = appdirs.user_cache_dir(appname='reviewbot',
                                                    appauthor='Beanbag')

        self.assertEqual(cookie_dir, default_cookie_dir)
        self.assertEqual(config['cookie_path'],
                         os.path.join(cookie_dir, 'reviewbot-cookies.txt'))

        self.assertSpyCalledWith(
            logger.error,
            'cookie_dir was empty in %s. Using the default of %s instead.',
            config_file,
            default_cookie_dir)

    def test_load_config_with_rel_cookie_dir(self):
        """Testing load_config with relative cookie_dir setting"""
        config_file = self._load_custom_config('cookie_dir = "./cookies/"\n')

        cookie_dir = config['cookie_dir']
        default_cookie_dir = appdirs.user_cache_dir(appname='reviewbot',
                                                    appauthor='Beanbag')

        self.assertEqual(cookie_dir, default_cookie_dir)
        self.assertEqual(config['cookie_path'],
                         os.path.join(cookie_dir, 'reviewbot-cookies.txt'))

        self.assertSpyCalledWith(
            logger.error,
            'cookie_dir (%s) must be a relative path in %s. Using the '
            'default of %s instead.',
            './cookies/',
            config_file,
            default_cookie_dir)

    def test_load_config_with_reviewboard_servers_config_path(self):
        """Testing load_config with reviewboard_servers_config_path"""
        fd, servers_path = tempfile.mkstemp()

        with os.fdopen(fd, 'w') as fp:
            json.dump(
                [
                    {
                        'url': 'https://rb1.example.com/',
                    },
                    {
                        'url': 'https://rb2.example.com/',
                        'user': 'my-user',
                        'token': 'abc123',
                    },
                ],
                fp)

        self._load_custom_config(
            'reviewboard_servers_config_path = "%(servers_path)s"\n'
            % {
                'servers_path': servers_path,
            }
        )

        os.remove(servers_path)

        self.assertEqual(
            config['reviewboard_servers'],
            [
                {
                    'url': 'https://rb1.example.com/',
                },
                {
                    'url': 'https://rb2.example.com/',
                    'user': 'my-user',
                    'token': 'abc123',
                },
            ])

        self.assertSpyNotCalled(logger.error)
        self.assertSpyNotCalled(logger.warning)

    def test_load_config_with_reviewboard_servers_config_path_merge(self):
        """Testing load_config with reviewboard_servers_config_path merges with
        reviewboard_servers
        """
        fd, servers_path = tempfile.mkstemp()

        with os.fdopen(fd, 'w') as fp:
            json.dump(
                [
                    {
                        'url': 'https://rb2.example.com/',
                    },
                    {
                        'url': 'https://rb3.example.com/',
                        'user': 'my-user',
                        'token': 'abc123',
                    },
                ],
                fp)

        self._load_custom_config(
            'reviewboard_servers = [{\n'
            '    "url": "https://rb1.example.com/",\n'
            '}]\n'
            '\n'
            'reviewboard_servers_config_path = "%(servers_path)s"\n'
            % {
                'servers_path': servers_path,
            }
        )

        os.remove(servers_path)

        self.assertEqual(
            config['reviewboard_servers'],
            [
                {
                    'url': 'https://rb1.example.com/',
                },
                {
                    'url': 'https://rb2.example.com/',
                },
                {
                    'url': 'https://rb3.example.com/',
                    'user': 'my-user',
                    'token': 'abc123',
                },
            ])

        self.assertSpyNotCalled(logger.error)
        self.assertSpyNotCalled(logger.warning)

    def test_load_config_with_reviewboard_servers_config_path_with_empty(self):
        """Testing load_config with reviewboard_servers_config_path with empty
        file
        """
        fd, servers_path = tempfile.mkstemp()

        with os.fdopen(fd, 'w') as fp:
            json.dump([], fp)

        self._load_custom_config(
            'reviewboard_servers = [{\n'
            '    "url": "https://rb1.example.com/",\n'
            '}]\n'
            '\n'
            'reviewboard_servers_config_path = "%(servers_path)s"\n'
            % {
                'servers_path': servers_path,
            }
        )

        os.remove(servers_path)

        self.assertEqual(
            config['reviewboard_servers'],
            [
                {
                    'url': 'https://rb1.example.com/',
                },
            ])

        self.assertSpyNotCalled(logger.error)
        self.assertSpyNotCalled(logger.warning)

    def test_load_config_with_reviewboard_servers_config_path_not_found(self):
        """Testing load_config with reviewboard_servers_config_path file not
        found
        """
        self._load_custom_config(
            'reviewboard_servers = [{\n'
            '    "url": "https://rb1.example.com/",\n'
            '}]\n'
            '\n'
            'reviewboard_servers_config_path = "/xxx/rb-servers"\n'
        )

        self.assertEqual(
            config['reviewboard_servers'],
            [
                {
                    'url': 'https://rb1.example.com/',
                },
            ])

        self.assertSpyCalledWith(
            logger.warning,
            'The Review Board servers configuration file "%s" was not found. '
            'If you aren\'t using tools that require full-repository access, '
            'you can ignore this.',
            '/xxx/rb-servers')
        self.assertSpyNotCalled(logger.error)

    def test_load_config_with_reviewboard_servers_config_path_bad_format(self):
        """Testing load_config with reviewboard_servers_config_path file with
        a bad format
        """
        fd, servers_path = tempfile.mkstemp()

        with os.fdopen(fd, 'w') as fp:
            json.dump({}, fp)

        self._load_custom_config(
            'reviewboard_servers = [{\n'
            '    "url": "https://rb1.example.com/",\n'
            '}]\n'
            '\n'
            'reviewboard_servers_config_path = "%(servers_path)s"\n'
            % {
                'servers_path': servers_path,
            }
        )

        self.assertEqual(
            config['reviewboard_servers'],
            [
                {
                    'url': 'https://rb1.example.com/',
                },
            ])

        self.assertSpyCalledWith(
            logger.error,
            'The configuration file at %s must contain a list, not a %s.',
            servers_path,
            'dict')
        self.assertSpyNotCalled(logger.warning)

    def test_load_config_with_repositories_config_path(self):
        """Testing load_config with repositories_config_path"""
        fd, repos_path = tempfile.mkstemp()

        with os.fdopen(fd, 'w') as fp:
            json.dump(
                [
                    {
                        'clone_path': 'git@example.com:/repo1.git',
                        'name': 'repo1',
                    },
                    {
                        'clone_path': 'git@example.com:/repo2.git',
                        'name': 'repo2',
                        'type': 'git',
                    },
                ],
                fp)

        self._load_custom_config(
            'repositories_config_path = "%(repos_path)s"\n'
            % {
                'repos_path': repos_path,
            }
        )

        os.remove(repos_path)

        self.assertEqual(
            config['repositories'],
            [
                {
                    'clone_path': 'git@example.com:/repo1.git',
                    'name': 'repo1',
                },
                {
                    'clone_path': 'git@example.com:/repo2.git',
                    'name': 'repo2',
                    'type': 'git',
                },
            ])

        self.assertSpyNotCalled(logger.error)
        self.assertSpyNotCalled(logger.warning)

    def test_load_config_with_repositories_config_path_merge(self):
        """Testing load_config with repositories_config_path merges with
        repositories
        """
        fd, repos_path = tempfile.mkstemp()

        with os.fdopen(fd, 'w') as fp:
            json.dump(
                [
                    {
                        'clone_path': 'git@example.com:/repo2.git',
                        'name': 'repo2',
                    },
                    {
                        'clone_path': 'git@example.com:/repo3.git',
                        'name': 'repo3',
                        'type': 'git',
                    },
                ],
                fp)

        self._load_custom_config(
            'repositories = [{\n'
            '    "clone_path": "git@example.com:/repo1.git",\n'
            '    "name": "repo1",\n'
            '}]\n'
            '\n'
            'repositories_config_path = "%(repos_path)s"\n'
            % {
                'repos_path': repos_path,
            }
        )

        os.remove(repos_path)

        self.assertEqual(
            config['repositories'],
            [
                {
                    'clone_path': 'git@example.com:/repo1.git',
                    'name': 'repo1',
                },
                {
                    'clone_path': 'git@example.com:/repo2.git',
                    'name': 'repo2',
                },
                {
                    'clone_path': 'git@example.com:/repo3.git',
                    'name': 'repo3',
                    'type': 'git',
                },
            ])

        self.assertSpyNotCalled(logger.error)
        self.assertSpyNotCalled(logger.warning)

    def test_load_config_with_repositories_config_path_with_empty(self):
        """Testing load_config with repositories_config_path with empty file"""
        fd, repos_path = tempfile.mkstemp()

        with os.fdopen(fd, 'w') as fp:
            json.dump([], fp)

        self._load_custom_config(
            'repositories = [{\n'
            '    "clone_path": "git@example.com:/repo1.git",\n'
            '    "name": "repo1",\n'
            '}]\n'
            '\n'
            'repositories_config_path = "%(repos_path)s"\n'
            % {
                'repos_path': repos_path,
            }
        )

        os.remove(repos_path)

        self.assertEqual(
            config['repositories'],
            [
                {
                    'clone_path': 'git@example.com:/repo1.git',
                    'name': 'repo1',
                },
            ])

        self.assertSpyNotCalled(logger.error)
        self.assertSpyNotCalled(logger.warning)

    def test_load_config_with_repositories_config_path_not_found(self):
        """Testing load_config with repositories_config_path file not found"""
        self._load_custom_config(
            'repositories = [{\n'
            '    "clone_path": "git@example.com:/repo1.git",\n'
            '    "name": "repo1",\n'
            '}]\n'
            '\n'
            'repositories_config_path = "/xxx/repos"\n'
        )

        self.assertEqual(
            config['repositories'],
            [
                {
                    'clone_path': 'git@example.com:/repo1.git',
                    'name': 'repo1',
                },
            ])

        self.assertSpyCalledWith(
            logger.warning,
            'The repository configuration file "%s" was not found. If you '
            'aren\'t using tools that require full-repository access, you '
            'can ignore this.',
            '/xxx/repos')
        self.assertSpyNotCalled(logger.error)

    def test_load_config_with_repositories_config_path_bad_format(self):
        """Testing load_config with repositories_config_path file with a bad
        format
        """
        fd, repos_path = tempfile.mkstemp()

        with os.fdopen(fd, 'w') as fp:
            json.dump({}, fp)

        self._load_custom_config(
            'repositories = [{\n'
            '    "clone_path": "git@example.com:/repo1.git",\n'
            '    "name": "repo1",\n'
            '}]\n'
            '\n'
            'repositories_config_path = "%(repos_path)s"\n'
            % {
                'repos_path': repos_path,
            }
        )

        self.assertEqual(
            config['repositories'],
            [
                {
                    'clone_path': 'git@example.com:/repo1.git',
                    'name': 'repo1',
                },
            ])

        self.assertSpyCalledWith(
            logger.error,
            'The configuration file at %s must contain a list, not a %s.',
            repos_path,
            'dict')
        self.assertSpyNotCalled(logger.warning)

    def _load_custom_config(self, config_contents):
        """Load a custom configuration file.

        This will write the file to a path and force it to be used as the
        default-loaded configuration file.

        Args:
            config_contents (unicode):
                The configuration file contents.

        Returns:
            unicode:
            The path to the configuration file.
        """
        tempdir = tempfile.mkdtemp()
        config_file = os.path.join(tempdir, 'config.py')

        try:
            with open(config_file, 'w') as fp:
                fp.write(config_contents)

            self.spy_on(appdirs.site_config_dir,
                        op=kgb.SpyOpReturn(tempdir))

            load_config()
        finally:
            shutil.rmtree(tempdir)

        return config_file
