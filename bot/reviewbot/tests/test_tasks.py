"""Unit tests for reviewbot.tasks."""

from __future__ import unicode_literals

import kgb
from celery.worker.control import Panel
from rbtools.api.errors import APIError, AuthorizationError

from reviewbot.processing.review import Review
from reviewbot.repositories import GitRepository, repositories
from reviewbot.tasks import RunTool, update_tools_list
from reviewbot.testing import TestCase
from reviewbot.testing.testcases import (ReviewBotToolsResource,
                                         StatusUpdateResource)
from reviewbot.tools import Tool
from reviewbot.tools.base import BaseTool
from reviewbot.tools.base.registry import (_registered_tools,
                                           register_tool_class,
                                           unregister_tool_class)
from reviewbot.utils.api import get_api_root


class LegacyTool(Tool):
    name = 'Legacy'
    tool_id = 'legacy'
    description = 'This is the legacy tool.'
    timeout = 30


class DummyTool(BaseTool):
    name = 'Dummy'
    tool_id = 'dummy'
    description = 'This is the dummy tool.'
    options = [
        {
            'name': 'some_option',
            'field_type': 'django.forms.CharField',
            'default': '123',
        },
    ]


class FullRepoTool(BaseTool):
    name = 'FullRepo'
    tool_id = 'full-repo'
    description = 'This is the full repository tool.'
    working_directory_required = True
    timeout = 60
    version = '2'


class FailedDepCheckTool(BaseTool):
    name = 'FailedDepCheck'
    tool_id = 'failed-dep-check'
    description = 'This is the failed dependency check tool.'
    exe_dependencies = ['xxx-bad-dep']


class BaseTaskTestCase(kgb.SpyAgency, TestCase):
    @classmethod
    def setUpClass(cls):
        super(BaseTaskTestCase, cls).setUpClass()

        _registered_tools.clear()
        register_tool_class(DummyTool)
        register_tool_class(LegacyTool)
        register_tool_class(FullRepoTool)
        register_tool_class(FailedDepCheckTool)

    @classmethod
    def tearDownClass(cls):
        super(BaseTaskTestCase, cls).tearDownClass()

        unregister_tool_class(DummyTool.tool_id)
        unregister_tool_class(LegacyTool.tool_id)
        unregister_tool_class(FullRepoTool.tool_id)
        unregister_tool_class(FailedDepCheckTool.tool_id)

    def call_task(self, task, delivery_info={}, **kwargs):
        """Call a task.

        This handles patching in delivery information for the task, and will
        force any exceptions to bubble up rather than being swallowed by the
        task runner.

        Args:
            task (object):
                The task object/function being run.

            delivery_info (dict, optional):
                Custom delivery information to provide.

            **kwargs (dict):
                Additional keyword arguments to provide for the task.

        Returns:
            object:
            The result of the task.
        """
        if delivery_info:
            @self.spy_for(task.run)
            def _run(*args, **kwargs):
                task.request.delivery_info.update(delivery_info)

                return task.run.call_original(*args, **kwargs)

        kwargs['throw'] = True
        return task.apply(kwargs=kwargs).get()


class RunToolTests(BaseTaskTestCase):
    """Unit tests for reviewbot.tasks.RunTool."""

    def setUp(self):
        super(RunToolTests, self).setUp()

        self.spy_on(get_api_root,
                    op=kgb.SpyOpReturn(self.api_root))
        self.spy_on(DummyTool.execute,
                    owner=DummyTool)
        self.spy_on(StatusUpdateResource.update,
                    owner=StatusUpdateResource)
        self.spy_on(Review.publish,
                    owner=Review)

    def test_with_no_comments(self):
        """Testing RunTool task with no comments"""
        result = self.run_tools_task(
            routing_key=DummyTool.tool_id,
            tool_options={
                'option1': 'value1',
                'option2': 'value2',
            })

        self.assertTrue(result)
        self.assertSpyCalledWith(
            DummyTool.execute,
            base_commit_id='',
            repository=None,
            settings={
                'option1': 'value1',
                'option2': 'value2',
            })

        self.assertSpyCalledWith(StatusUpdateResource.update,
                                 description='running...')
        self.assertSpyCalledWith(StatusUpdateResource.update,
                                 state='done-success',
                                 description='passed.')
        self.assertSpyCallCount(StatusUpdateResource.update, 2)

    def test_with_diff_comments(self):
        """Testing RunTool task with diff comments"""
        @self.spy_for(DummyTool.handle_file, owner=DummyTool)
        def _handle_file(_self, f, *args, **kwargs):
            f.comment('Bad line!', first_line=1)

        self.spy_on(
            self.api_root.get_files,
            op=kgb.SpyOpReturn([self.create_filediff_resource()]))

        result = self.run_tools_task(routing_key=DummyTool.tool_id)

        self.assertTrue(result)
        self.assertSpyCalledWith(DummyTool.execute,
                                 repository=None,
                                 base_commit_id='')
        self.assertSpyCalled(Review.publish)

        self.assertSpyCalledWith(StatusUpdateResource.update,
                                 description='running...')
        self.assertSpyCalledWith(StatusUpdateResource.update,
                                 state='done-failure',
                                 description='failed.',
                                 review_id=123)
        self.assertSpyCallCount(StatusUpdateResource.update, 2)

    def test_with_general_comments(self):
        """Testing RunTool task with general comments"""
        DummyTool.execute.unspy()

        @self.spy_for(DummyTool.execute, owner=DummyTool)
        def _execute(_self, review, **kwargs):
            review.general_comment('Bad thing!')

        result = self.run_tools_task(routing_key=DummyTool.tool_id)

        self.assertTrue(result)
        self.assertSpyCalledWith(DummyTool.execute,
                                 base_commit_id='',
                                 repository=None)
        self.assertSpyCalled(Review.publish)

        self.assertSpyCalledWith(StatusUpdateResource.update,
                                 description='running...')
        self.assertSpyCalledWith(StatusUpdateResource.update,
                                 state='done-failure',
                                 description='failed.',
                                 review_id=123)
        self.assertSpyCallCount(StatusUpdateResource.update, 2)

    def test_with_text_output(self):
        """Testing RunTool task with text output attachment"""
        DummyTool.execute.unspy()

        @self.spy_for(DummyTool.execute, owner=DummyTool)
        def _execute(_self, review, **kwargs):
            _self.output = 'This is sure some output!'

        result = self.run_tools_task(routing_key=DummyTool.tool_id)

        self.assertTrue(result)
        self.assertSpyCalledWith(DummyTool.execute,
                                 base_commit_id='',
                                 repository=None)

        self.assertSpyCalledWith(StatusUpdateResource.update,
                                 description='running...')
        self.assertSpyCalledWith(StatusUpdateResource.update,
                                 url='/path/to/attachment.txt',
                                 url_text='Tool console output')
        self.assertSpyCalledWith(StatusUpdateResource.update,
                                 state='done-success',
                                 description='passed.')
        self.assertSpyCallCount(StatusUpdateResource.update, 3)

    def test_with_full_repo_tool(self):
        """Testing RunTool task with full-repository tool"""
        self.spy_on(FullRepoTool.execute,
                    owner=FullRepoTool)

        repositories['MyRepo'] = GitRepository(
            name='MyRepo',
            clone_path='git://example.com/repo')

        try:
            result = self.run_tools_task(base_commit_id='abc123',
                                         routing_key=FullRepoTool.tool_id,
                                         repository_name='MyRepo')
        finally:
            repositories.clear()

        self.assertTrue(result)
        self.assertSpyCalledWith(FullRepoTool.execute,
                                 base_commit_id='abc123')

        repository = FullRepoTool.execute.last_call.kwargs['repository']
        self.assertIsNotNone(repository)
        self.assertIsInstance(repository, GitRepository)
        self.assertEqual(repository.name, 'MyRepo')

        self.assertSpyCalledWith(StatusUpdateResource.update,
                                 description='running...')
        self.assertSpyCalledWith(StatusUpdateResource.update,
                                 state='done-success',
                                 description='passed.')
        self.assertSpyCallCount(StatusUpdateResource.update, 2)

    def test_with_legacy_tool(self):
        """Testing RunTool task with legacy tool"""
        self.spy_on(LegacyTool.execute,
                    owner=LegacyTool)

        result = self.run_tools_task(
            routing_key=LegacyTool.tool_id,
            tool_options={
                'option1': 'value1',
                'option2': 'value2',
            })

        self.assertTrue(result)
        self.assertSpyCalledWith(
            LegacyTool.execute,
            base_commit_id='',
            repository=None,
            settings={
                'option1': 'value1',
                'option2': 'value2',
            })

        self.assertSpyCalledWith(StatusUpdateResource.update,
                                 description='running...')
        self.assertSpyCalledWith(StatusUpdateResource.update,
                                 state='done-success',
                                 description='passed.')
        self.assertSpyCallCount(StatusUpdateResource.update, 2)

    def test_with_base_commit_id(self):
        """Testing RunTool task with base_commit_id"""
        result = self.run_tools_task(base_commit_id='abc123',
                                     routing_key=DummyTool.tool_id)

        self.assertTrue(result)
        self.assertSpyCalledWith(DummyTool.execute,
                                 base_commit_id='abc123',
                                 repository=None,
                                 settings={})

        self.assertSpyCalledWith(StatusUpdateResource.update,
                                 description='running...')
        self.assertSpyCalledWith(StatusUpdateResource.update,
                                 state='done-success',
                                 description='passed.')
        self.assertSpyCallCount(StatusUpdateResource.update, 2)

    def test_with_error_contacting_rb_api(self):
        """Testing RunTool task with error contacting Review Board API"""
        get_api_root.unspy()
        self.spy_on(get_api_root,
                    op=kgb.SpyOpRaise(AuthorizationError(http_status=401,
                                                         error_code=103)))

        result = self.run_tools_task(routing_key=DummyTool.tool_id)

        self.assertFalse(result)
        self.assertSpyNotCalled(DummyTool.execute)
        self.assertSpyNotCalled(StatusUpdateResource.update)

    def test_with_error_finding_tool(self):
        """Testing RunTool task with error finding requested tool"""
        result = self.run_tools_task(routing_key='bad-tool')

        self.assertFalse(result)
        self.assertSpyNotCalled(DummyTool.execute)
        self.assertSpyNotCalled(StatusUpdateResource.update)

    def test_with_error_init_tool(self):
        """Testing RunTool task with error initializing tool"""
        self.spy_on(DummyTool.__init__,
                    owner=DummyTool,
                    op=kgb.SpyOpRaise(Exception('oh no')))

        result = self.run_tools_task(routing_key=DummyTool.tool_id)

        self.assertFalse(result)
        self.assertSpyNotCalled(DummyTool.execute)

        self.assertSpyCalledWith(StatusUpdateResource.update,
                                 description='running...')
        self.assertSpyCalledWith(StatusUpdateResource.update,
                                 state='error',
                                 description='internal error.')
        self.assertSpyCallCount(StatusUpdateResource.update, 2)

    def test_with_error_execute_tool(self):
        """Testing RunTool task with error executing tool"""
        DummyTool.execute.unspy()
        self.spy_on(DummyTool.execute,
                    owner=DummyTool,
                    op=kgb.SpyOpRaise(Exception('oh no')))

        result = self.run_tools_task(routing_key=DummyTool.tool_id)

        self.assertFalse(result)
        self.assertSpyCalled(DummyTool.execute)

        self.assertSpyCalledWith(StatusUpdateResource.update,
                                 description='running...')
        self.assertSpyCalledWith(StatusUpdateResource.update,
                                 state='error',
                                 description='internal error.')
        self.assertSpyCallCount(StatusUpdateResource.update, 2)

    def test_with_error_creating_status_update(self):
        """Testing RunTool task with error creating status update"""
        self.spy_on(self.api_root.get_status_update,
                    op=kgb.SpyOpRaise(APIError(http_status=404,
                                               error_code=100)))

        result = self.run_tools_task(routing_key=DummyTool.tool_id)

        self.assertFalse(result)
        self.assertSpyNotCalled(DummyTool.execute)
        self.assertSpyNotCalled(StatusUpdateResource.update)

    def test_with_error_creating_review(self):
        """Testing RunTool task with error creating Review object"""
        self.spy_on(Review.__init__,
                    owner=Review,
                    op=kgb.SpyOpRaise(Exception('oh no')))

        result = self.run_tools_task(routing_key=DummyTool.tool_id)

        self.assertFalse(result)
        self.assertSpyNotCalled(DummyTool.execute)

        self.assertSpyCalledWith(StatusUpdateResource.update,
                                 state='error',
                                 description='internal error.')
        self.assertSpyCallCount(StatusUpdateResource.update, 1)

    def test_with_error_invalid_repository(self):
        """Testing RunTool task with error finding requested repository"""
        result = self.run_tools_task(base_commit_id='abc123',
                                     repository_name='MyRepo',
                                     routing_key=FullRepoTool.tool_id)

        self.assertFalse(result)
        self.assertSpyNotCalled(DummyTool.execute)
        self.assertSpyNotCalled(StatusUpdateResource.update)

    def test_with_error_repository_without_base_commit_id(self):
        """Testing RunTool task with error with repository but no
        base_commit_id
        """
        result = self.run_tools_task(routing_key=FullRepoTool.tool_id)

        self.assertFalse(result)
        self.assertSpyNotCalled(DummyTool.execute)
        self.assertSpyCalledWith(StatusUpdateResource.update,
                                 state='error',
                                 description='Diff does not include parent '
                                             'commit information.')

    def run_tools_task(self, routing_key, **kwargs):
        """Call the RunTools.

        This starts off with some common arguments for the task, and allows
        the caller to provide custom arguments specific to the test being
        performed.

        Args:
            routing_key (unicode):
                The routing key to pass for the task.

            **kwargs (dict):
                Additional keyword arguments to provide for the task.

        Returns:
            object:
            The result of the task.
        """
        task_kwargs = {
            'delivery_info': {
                'routing_key': routing_key,
            },
            'diff_revision': 1,
            'review_request_id': 123,
            'review_settings': {
                'comment_unmodified': False,
                'max_comments': 100,
                'open_issues': True,
            },
            'server_url': 'https://reviews.example.com/',
        }
        task_kwargs.update(kwargs)

        return self.call_task(RunTool, **task_kwargs)


class UpdateToolsListTests(BaseTaskTestCase):
    """Unit tests for reviewbot.tasks.update_tools_list."""

    @classmethod
    def setUpClass(cls):
        super(UpdateToolsListTests, cls).setUpClass()

        cls.panel = Panel()
        cls.panel.hostname = 'reviews.example.com'

    def setUp(self):
        super(UpdateToolsListTests, self).setUp()

        self.spy_on(get_api_root,
                    op=kgb.SpyOpReturn(self.api_root))

    def test_with_success(self):
        """Testing update_tools_list with successful result"""
        result = update_tools_list(
            panel=self.panel,
            payload={
                'session': 'session123',
                'url': 'https://reviews.example.com/',
            })

        # This should not include FailedDepCheckTool.
        self.assertEqual(result, {
            'status': 'ok',
            'tools': [
                {
                    'description': 'This is the dummy tool.',
                    'entry_point': 'dummy',
                    'name': 'Dummy',
                    'timeout': None,
                    'tool_options': (
                        '[{'
                        '"default": "123", '
                        '"field_type": "django.forms.CharField", '
                        '"name": "some_option"'
                        '}]'
                    ),
                    'version': '1',
                    'working_directory_required': False,
                },
                {
                    'description': 'This is the full repository tool.',
                    'entry_point': 'full-repo',
                    'name': 'FullRepo',
                    'timeout': 60,
                    'tool_options': '[]',
                    'version': '2',
                    'working_directory_required': True,
                },
                {
                    'description': 'This is the legacy tool.',
                    'entry_point': 'legacy',
                    'name': 'Legacy',
                    'timeout': 30,
                    'tool_options': '[]',
                    'version': '1',
                    'working_directory_required': False,
                },
            ],
        })

    def test_with_error_contacting_rb_api(self):
        """Testing update_tools_list task with error contacting Review Board
        API
        """
        get_api_root.unspy()
        self.spy_on(get_api_root,
                    op=kgb.SpyOpRaise(AuthorizationError(http_status=401,
                                                         error_code=103)))

        result = update_tools_list(
            panel=self.panel,
            payload={
                'session': 'session123',
                'url': 'https://reviews.example.com/',
            })

        # This should not include FailedDepCheckTool.
        self.assertEqual(result, {
            'error': (
                'Could not reach Review Board server: Error authenticating '
                'to Review Board. (API Error 103: Not Logged In)'
            ),
            'status': 'error',
        })

    def test_with_error_creating_tool(self):
        """Testing update_tools_list task with error creating tools via API"""
        self.spy_on(ReviewBotToolsResource.create,
                    owner=ReviewBotToolsResource,
                    op=kgb.SpyOpRaise(APIError(http_status=404,
                                               error_code=100)))

        result = update_tools_list(
            panel=self.panel,
            payload={
                'session': 'session123',
                'url': 'https://reviews.example.com/',
            })

        # This should not include FailedDepCheckTool.
        self.assertEqual(result, {
            'error': (
                'Problem uploading tools: An error occurred when '
                'communicating with Review Board. (API Error 100: Does Not '
                'Exist)'
            ),
            'status': 'error',
        })
