"""Unit tests for reviewbot.repositories."""

from __future__ import unicode_literals

import kgb

from reviewbot.config import config
from reviewbot.repositories import (GitRepository,
                                    HgRepository,
                                    init_repositories,
                                    logger,
                                    repositories,
                                    reset_repositories)
from reviewbot.testing.testcases import (DummyRootResource,
                                         RepositoryListResource,
                                         TestCase)
from reviewbot.utils.api import get_api_root


class RepositoriesTests(kgb.SpyAgency, TestCase):
    """Unit tests for reviewbot.repositories."""

    def tearDown(self):
        super(RepositoriesTests, self).tearDown()

        reset_repositories()

    def test_init_repositories_with_servers(self):
        """Testing init_repositories with reviewboard_servers"""
        api_transport = self.api_transport

        # Set up our API resource tree for rb1.example.com.
        rb1_url = 'https://rb1.example.com/'
        api_root1 = DummyRootResource(
            transport=api_transport,
            payload={
                'uri_templates': {},
            },
            url=rb1_url)

        self.spy_on(
            api_root1.get_repositories,
            op=kgb.SpyOpMatchAny([
                {
                    'kwargs': {
                        'tool': 'Mercurial',
                    },
                    'op': kgb.SpyOpReturn(RepositoryListResource(
                        transport=api_transport,
                        payload={
                            'repositories': [{
                                'name': 'Mercurial Repo 1',
                                'path': 'https://hg1.example.com/',
                                'mirror_path': '',
                            }],
                            'total_results': 1,
                        },
                        url='%srepositories/?tool=Mercurial' % rb1_url)),
                },
                {
                    'kwargs': {
                        'tool': 'Git',
                    },
                    'op': kgb.SpyOpReturn(RepositoryListResource(
                        transport=api_transport,
                        payload={
                            'repositories': [
                                {
                                    'name': 'Git Repo 1',
                                    'path': 'git@example.com:/repo1.git',
                                    'mirror_path': '',
                                },
                                {
                                    'name': 'Git Repo 2',
                                    'path': 'xxx',
                                    'mirror_path': 'git://example.com/repo2',
                                },
                            ],
                            'total_results': 2,
                        },
                        url='%srepositories/?tool=Git' % rb1_url)),
                },
            ]))

        # Set up our API resource tree for rb2.example.com.
        rb2_url = 'https://rb2.example.com/'
        api_root2 = DummyRootResource(
            transport=api_transport,
            payload={
                'uri_templates': {},
            },
            url=rb2_url)

        self.spy_on(
            api_root2.get_repositories,
            op=kgb.SpyOpMatchAny([
                {
                    'kwargs': {
                        'tool': 'Mercurial',
                    },
                    'op': kgb.SpyOpReturn(RepositoryListResource(
                        transport=api_transport,
                        payload={
                            'repositories': [{
                                'name': 'Mercurial Repo 2',
                                'path': 'https://hg2.example.com/',
                                'mirror_path': '',
                            }],
                            'total_results': 1,
                        },
                        url='%srepositories/?tool=Mercurial' % rb2_url)),
                },
                {
                    'kwargs': {
                        'tool': 'Git',
                    },
                    'op': kgb.SpyOpReturn(RepositoryListResource(
                        transport=api_transport,
                        payload={
                            'repositories': [],
                            'total_results': 0,
                        },
                        url='%srepositories/?tool=Git' % rb2_url)),
                },
            ]))

        # Dispatch to the correct root resource for the given server URL.
        self.spy_on(
            get_api_root,
            op=kgb.SpyOpMatchAny([
                {
                    'kwargs': {
                        'url': rb1_url,
                    },
                    'op': kgb.SpyOpReturn(api_root1),
                },
                {
                    'kwargs': {
                        'url': rb2_url,
                        'username': 'test-user',
                        'api_token': 'abc123',
                    },
                    'op': kgb.SpyOpReturn(api_root2),
                },
            ]))

        config['reviewboard_servers'] = [
            {
                'url': rb1_url,
            },
            {
                'url': rb2_url,
                'user': 'test-user',
                'token': 'abc123',
            },
        ]

        init_repositories()

        self.assertEqual(
            repositories,
            {
                'Git Repo 1': GitRepository(
                    name='Git Repo 1',
                    clone_path='git@example.com:/repo1.git'),
                'Git Repo 2': GitRepository(
                    name='Git Repo 2',
                    clone_path='git://example.com/repo2'),
                'Mercurial Repo 1': HgRepository(
                    name='Mercurial Repo 1',
                    clone_path='https://hg1.example.com/'),
                'Mercurial Repo 2': HgRepository(
                    name='Mercurial Repo 2',
                    clone_path='https://hg2.example.com/'),
            })

    def test_init_repositories_with_servers_missing_keys(self):
        """Testing init_repositories with reviewboard_servers containing
        missing keys
        """
        self.spy_on(logger.error)

        api_transport = self.api_transport

        # Set up our API resource tree for rb1.example.com.
        rb_url = 'https://rb1.example.com/'
        api_root = DummyRootResource(
            transport=api_transport,
            payload={
                'uri_templates': {},
            },
            url=rb_url)

        self.spy_on(
            api_root.get_repositories,
            op=kgb.SpyOpMatchAny([
                {
                    'kwargs': {
                        'tool': 'Git',
                    },
                    'op': kgb.SpyOpReturn(RepositoryListResource(
                        transport=api_transport,
                        payload={
                            'repositories': [],
                            'total_results': 0,
                        },
                        url='%srepositories/?tool=Git' % rb_url)),
                },
                {
                    'kwargs': {
                        'tool': 'Mercurial',
                    },
                    'op': kgb.SpyOpReturn(RepositoryListResource(
                        transport=api_transport,
                        payload={
                            'repositories': [{
                                'name': 'Mercurial Repo 1',
                                'path': 'https://hg1.example.com/',
                                'mirror_path': '',
                            }],
                            'total_results': 1,
                        },
                        url='%srepositories/?tool=Mercurial' % rb_url)),
                },
            ]))

        self.spy_on(get_api_root,
                    op=kgb.SpyOpReturn(api_root))

        repo_config2 = {
            'user': 'test-user',
        }

        config['reviewboard_servers'] = [
            {
                'url': rb_url,
                'user': 'test-user',
                'token': 'abc123',
            },
            repo_config2,
        ]

        init_repositories()

        self.assertEqual(
            repositories,
            {
                'Mercurial Repo 1': HgRepository(
                    name='Mercurial Repo 1',
                    clone_path='https://hg1.example.com/'),
            })

        self.assertSpyCalledWith(
            logger.error,
            'The following server configuration is missing the "url" key: %r',
            repo_config2)

    def test_init_repositories_with_repositories(self):
        """Testing init_repositories with repositories"""
        config['repositories'] = [
            {
                'name': 'repo1',
                'clone_path': 'git@example.com:/repo1.git',
                'type': 'git',
            },
            {
                'name': 'repo2',
                'clone_path': 'git@example.com:/repo2.git',
                'type': 'git',
            },
            {
                'name': 'repo3',
                'clone_path': 'https://hg.example.com/',
                'type': 'hg',
            },
        ]

        init_repositories()

        self.assertEqual(
            repositories,
            {
                'repo1': GitRepository(
                    name='repo1',
                    clone_path='git@example.com:/repo1.git'),
                'repo2': GitRepository(
                    name='repo2',
                    clone_path='git@example.com:/repo2.git'),
                'repo3': HgRepository(
                    name='repo3',
                    clone_path='https://hg.example.com/'),
            })

    def test_init_repositories_with_repositories_missing_keys(self):
        """Testing init_repositories with repositories containing missing keys
        """
        self.spy_on(logger.error)

        repo_config1 = {
            'name': 'repo1',
            'clone_path': 'git@example.com:/repo1.git',
        }

        repo_config2 = {
            'name': 'repo2',
        }

        config['repositories'] = [
            repo_config1,
            repo_config2,
            {
                'name': 'repo3',
                'clone_path': 'https://hg.example.com/',
                'type': 'hg',
            },
        ]

        init_repositories()

        self.assertEqual(
            repositories,
            {
                'repo3': HgRepository(
                    name='repo3',
                    clone_path='https://hg.example.com/'),
            })

        self.assertSpyCalledWith(
            logger.error,
            'The following repository configuration is missing the %s '
            'key(s): %r',
            '"type"',
            repo_config1)
        self.assertSpyCalledWith(
            logger.error,
            'The following repository configuration is missing the %s '
            'key(s): %r',
            '"clone_path", "type"',
            repo_config2)
