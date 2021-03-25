"""Unit tests for reviewbot.config."""

from __future__ import unicode_literals

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
        tempdir = tempfile.mkdtemp()
        config_file = os.path.join(tempdir, 'config.py')

        try:
            with open(config_file, 'w') as fp:
                fp.write(
                    'reviewboard_servers = [{\n'
                    '    "url": "https://reviews2.example.com/",\n'
                    '}]\n'
                    'repositories = [{\n'
                    '    "name": "test",\n'
                    '    "clone_path": "git@example.com:/repo2.git",\n'
                    '}]\n'
                )

            self.spy_on(appdirs.site_config_dir,
                        op=kgb.SpyOpReturn(tempdir))

            load_config()
        finally:
            shutil.rmtree(tempdir)

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
            ('Review Bot configuration was not found at %s. Using the '
             'defaults.'),
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

    def test_load_config_with_deprecated_pmd_path(self):
        """Testing load_config with deprecated pmd_path setting"""
        tempdir = tempfile.mkdtemp()
        config_file = os.path.join(tempdir, 'config.py')

        try:
            with open(config_file, 'w') as fp:
                fp.write('pmd_path = "/path/to/pmd"\n')

            self.spy_on(appdirs.site_config_dir,
                        op=kgb.SpyOpReturn(tempdir))

            load_config()
        finally:
            shutil.rmtree(tempdir)

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
        tempdir = tempfile.mkdtemp()
        config_file = os.path.join(tempdir, 'config.py')

        try:
            with open(config_file, 'w') as fp:
                fp.write(
                    'review_board_servers = [{\n'
                    '    "url": "https://reviews2.example.com/",\n'
                    '}]\n'
                    'repositories = [{\n'
                    '    "name": "test",\n'
                    '    "clone_path": "git@example.com:/repo2.git",\n'
                    '}]\n'
                )

            self.spy_on(appdirs.site_config_dir,
                        op=kgb.SpyOpReturn(tempdir))

            load_config()
        finally:
            shutil.rmtree(tempdir)

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
            'in Review Bot 4.0. Please rename it to reviewboard_servers.',
            config_file)
        self.assertSpyNotCalled(logger.error)
