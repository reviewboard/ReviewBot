"""Unit tests for reviewbot.celery."""

from __future__ import unicode_literals

import os
import re
import shutil
import tempfile

import kgb

from reviewbot.celery import setup_cookies
from reviewbot.config import config
from reviewbot.testing import TestCase
from reviewbot.utils.log import get_root_logger


root_logger = get_root_logger()


class SetupCookiesTests(kgb.SpyAgency, TestCase):
    """Unit tests for reviewbot.celery.setup_cookies."""

    def setUp(self):
        super(SetupCookiesTests, self).setUp()

        self.cookie_root = tempfile.mkdtemp()
        self.cookie_dir = os.path.join(self.cookie_root, 'cookies')
        self.cookie_path = os.path.join(self.cookie_dir,
                                        'reviewbot-cookies.txt')

        os.mkdir(self.cookie_dir, 0o755)

        self.config = {
            'cookie_dir': self.cookie_dir,
            'cookie_path': self.cookie_path,
        }

        self.spy_on(root_logger.debug)

    def tearDown(self):
        super(SetupCookiesTests, self).tearDown()

        shutil.rmtree(self.cookie_root)

    def test_with_nonexistant_cookie_dir(self):
        """Testing setup_cookies with non-existant cookie directory"""
        os.rmdir(self.cookie_dir)

        with self.override_config(self.config):
            setup_cookies()

        self.assertTrue(os.path.exists(self.cookie_dir))
        self.assertTrue(os.path.exists(self.cookie_path))
        self.assertSpyCalledWith(
            root_logger.debug,
            'Checking cookie storage at %s',
            self.cookie_path)
        self.assertSpyCalledWith(
            root_logger.debug,
            'Cookies can be stored at %s',
            self.cookie_path)

    def test_with_nonexistant_cookie_dir_cant_create(self):
        """Testing setup_cookies with non-existant cookie directory that
        can't be created
        """
        cookie_path = '/dev/null/cookies/reviewbot-cookies.txt'

        new_config = {
            'cookie_dir': '/dev/null/cookies/',
            'cookie_path': cookie_path,
        }

        with self.override_config(new_config):
            expected_message = re.escape(
                'Unable to create cookies directory "/dev/null/cookies/":'
            )

            with self.assertRaisesRegexp(IOError, expected_message):
                setup_cookies()

        self.assertSpyCalledWith(
            root_logger.debug,
            'Checking cookie storage at %s',
            cookie_path)
        self.assertSpyNotCalledWith(
            root_logger.debug,
            'Cookies can be stored at %s',
            cookie_path)

    def test_with_existing_cookie_path_cant_write(self):
        """Testing setup_cookies with existing cookie file that can't be
        written to
        """
        cookie_path = self.cookie_path

        with self.override_config(self.config):
            with open(cookie_path, 'w'):
                pass

            os.chmod(cookie_path, 0o000)

            expected_message = re.escape(
                'Unable to write to cookie file "%s". Please make sure '
                'Review Bot has the proper permissions.'
                % cookie_path
            )

            with self.assertRaisesRegexp(IOError, expected_message):
                setup_cookies()

        self.assertSpyCalledWith(
            root_logger.debug,
            'Checking cookie storage at %s',
            cookie_path)
        self.assertSpyNotCalledWith(
            root_logger.debug,
            'Cookies can be stored at %s',
            cookie_path)

    def test_with_nonexistant_cookie_path_cant_write(self):
        """Testing setup_cookies with non-existant cookie file that can't be
        written to
        """
        cookie_path = self.cookie_path

        with self.override_config(self.config):
            os.chmod(config['cookie_dir'], 0o400)

            expected_message = re.escape(
                'Unable to write to cookie file "%s". Please make sure '
                'Review Bot has the proper permissions.'
                % cookie_path
            )

            with self.assertRaisesRegexp(IOError, expected_message):
                setup_cookies()

        self.assertSpyCalledWith(
            root_logger.debug,
            'Checking cookie storage at %s',
            cookie_path)
        self.assertSpyNotCalledWith(
            root_logger.debug,
            'Cookies can be stored at %s',
            cookie_path)
