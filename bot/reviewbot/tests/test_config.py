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
                'review_board_servers = [{\n'
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

        self.assertEqual(config['review_board_servers'], [
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

        self.assertEqual(config['review_board_servers'], [
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

        self.assertEqual(config['review_board_servers'], [])
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

        self.assertEqual(config['review_board_servers'], [])
        self.assertEqual(config['repositories'], [])

        self.assertSpyCalledWith(
            logger.info,
            'Loading Review Bot configuration file %s',
            os.path.join(tempdir, 'config.py'))
        self.assertSpyCalledWith(
            logger.error,
            'Unable to read the Review Bot configuration file: %s')
        self.assertSpyNotCalled(logger.warning)
