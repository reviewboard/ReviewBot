"""Unit tests for reviewbot.tools.base.mixins.JavaToolMixin."""

from __future__ import unicode_literals

import os

import kgb

from reviewbot.testing import TestCase
from reviewbot.tools.base.mixins import JavaToolMixin
from reviewbot.tools.base.tool import BaseTool
from reviewbot.utils.process import execute, is_exe_in_path


class MyJavaTool(JavaToolMixin, BaseTool):
    java_main = 'a.b.c.Main'
    java_classpaths_key = 'mytool'


class JavaToolMixinTests(kgb.SpyAgency, TestCase):
    """Unit tests for reviewbot.tools.base.mixins.JavaToolMixin."""

    def setUp(self):
        super(JavaToolMixinTests, self).setUp()

        self.tool = MyJavaTool()

    def test_build_base_command_with_classpath_config(self):
        """Testing JavaToolMixin.build_base_command with java_classpaths config
        """
        new_config = {
            'exe_paths': {
                'java': '/path/to/java',
            },
            'java_classpaths': {
                'mytool': [
                    '/path/to/foo.jar',
                    '/path/to/bar.jar',
                ],
            },
        }

        with self.override_config(new_config):
            self.assertEqual(
                self.tool.build_base_command(),
                [
                    '/path/to/java',
                    '-cp',
                    '/path/to/foo.jar:/path/to/bar.jar',
                    'a.b.c.Main',
                ])

    def test_build_base_command_with_no_classpath(self):
        """Testing JavaToolMixin.build_base_command with no java_classpaths
        config
        """
        new_config = {
            'exe_paths': {
                'java': '/path/to/java',
            },
        }

        with self.override_config(new_config):
            self.assertEqual(
                self.tool.build_base_command(),
                [
                    '/path/to/java',
                    'a.b.c.Main',
                ])

    def test_check_dependencies_with_found(self):
        """Testing JavaToolMixin.check_dependencies with all dependencies
        found
        """
        self.spy_on(is_exe_in_path,
                    op=kgb.SpyOpReturn(True))
        self.spy_on(self.tool._check_java_classpath,
                    op=kgb.SpyOpReturn(True))
        self.spy_on(execute,
                    op=kgb.SpyOpReturn('Run myprogram --help for info'))

        new_config = {
            'exe_paths': {
                'java': '/path/to/java',
            },
            'java_classpaths': {
                'mytool': ['/path/to/foo.jar'],
            },
        }

        with self.override_config(new_config):
            self.assertTrue(self.tool.check_dependencies())

        self.assertSpyCalledWith(
            is_exe_in_path,
            '/path/to/java',
            cache={
                'java': '/path/to/java',
            })
        self.assertSpyCalledWith(
            self.tool._check_java_classpath,
            ['/path/to/foo.jar'])
        self.assertSpyCalledWith(
            execute,
            [
                '/path/to/java',
                '-cp',
                '/path/to/foo.jar',
                'a.b.c.Main',
            ])

    def test_check_dependencies_with_java_not_found(self):
        """Testing JavaToolMixin.check_dependencies with java not found"""
        self.spy_on(is_exe_in_path,
                    op=kgb.SpyOpReturn(False))
        self.spy_on(self.tool._check_java_classpath,
                    op=kgb.SpyOpReturn(True))
        self.spy_on(execute,
                    op=kgb.SpyOpReturn('Run myprogram --help for info'))

        new_config = {
            'exe_paths': {
                'java': '/path/to/java',
            },
            'java_classpaths': {
                'mytool': ['/path/to/foo.jar'],
            },
        }

        with self.override_config(new_config):
            self.assertFalse(self.tool.check_dependencies())

        self.assertSpyCalledWith(
            is_exe_in_path,
            '/path/to/java',
            cache={
                'java': '/path/to/java',
            })
        self.assertSpyNotCalled(self.tool._check_java_classpath)
        self.assertSpyNotCalled(execute)

    def test_check_dependencies_with_class_not_found(self):
        """Testing JavaToolMixin.check_dependencies with main class not found
        """
        self.spy_on(is_exe_in_path,
                    op=kgb.SpyOpReturn(True))
        self.spy_on(self.tool._check_java_classpath,
                    op=kgb.SpyOpReturn(True))
        self.spy_on(
            execute,
            op=kgb.SpyOpReturnInOrder([
                'java version "1.8.0_60"\n',
                'Error: Could not find or load main class a.b.c.Main',
            ]))

        new_config = {
            'exe_paths': {
                'java': '/path/to/java',
            },
            'java_classpaths': {
                'mytool': ['/path/to/foo.jar'],
            },
        }

        JavaToolMixin.clear_has_java_runtime()

        try:
            with self.override_config(new_config):
                self.assertFalse(self.tool.check_dependencies())
        finally:
            JavaToolMixin.clear_has_java_runtime()

        self.assertSpyCalledWith(
            is_exe_in_path,
            '/path/to/java',
            cache={
                'java': '/path/to/java',
            })
        self.assertSpyCalledWith(
            is_exe_in_path,
            '/path/to/java',
            cache={
                'java': '/path/to/java',
            })
        self.assertSpyCalledWith(
            self.tool._check_java_classpath,
            ['/path/to/foo.jar'])
        self.assertSpyCalledWith(
            execute.calls[0],
            [
                '/path/to/java',
                '-version',
            ])
        self.assertSpyCalledWith(
            execute.calls[1],
            [
                '/path/to/java',
                '-cp',
                '/path/to/foo.jar',
                'a.b.c.Main',
            ])
