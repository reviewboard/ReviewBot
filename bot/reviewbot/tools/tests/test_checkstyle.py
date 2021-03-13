"""Unit tests for reviewbot.tools.checkstyle."""

from __future__ import unicode_literals

import kgb

from reviewbot.testing import TestCase
from reviewbot.tools.checkstyle import CheckstyleTool
from reviewbot.utils.process import is_exe_in_path


class CheckstyleToolTests(kgb.SpyAgency, TestCase):
    """Unit tests for reviewbot.tools.checkstyle.CheckstyleTool."""

    def test_check_dependencies_with_no_config(self):
        """Testing CheckstyleTool.check_dependencies with no configured
        checkstyle_path
        """
        with self.override_config({}):
            tool = CheckstyleTool()
            self.assertFalse(tool.check_dependencies())

    def test_check_dependencies_with_checkstyle_not_found(self):
        """Testing CheckstyleTool.check_dependencies with configured
        checkstyle_path not found on filesystem
        """
        self.spy_on(is_exe_in_path, op=kgb.SpyOpMatchInOrder([
            {
                'args': ('/path/to/checkstyle',),
                'call_fake': lambda path: False,
            },
            {
                'args': ('java',),
                'call_fake': lambda path: True,
            },
        ]))

        with self.override_config({'checkstyle_path': '/path/to/checkstyle'}):
            tool = CheckstyleTool()
            self.assertFalse(tool.check_dependencies())
            self.assertSpyCalledWith(is_exe_in_path, '/path/to/checkstyle')
            self.assertSpyCallCount(is_exe_in_path, 1)

    def test_check_dependencies_with_java_not_found(self):
        """Testing CheckstyleTool.check_dependencies with configured
        checkstyle_path found on filesystem but java not found
        """
        self.spy_on(is_exe_in_path, op=kgb.SpyOpMatchInOrder([
            {
                'args': ('/path/to/checkstyle',),
                'call_fake': lambda path: True,
            },
            {
                'args': ('java',),
                'call_fake': lambda path: False,
            },
        ]))

        with self.override_config({'checkstyle_path': '/path/to/checkstyle'}):
            tool = CheckstyleTool()
            self.assertFalse(tool.check_dependencies())
            self.assertSpyCalledWith(is_exe_in_path, '/path/to/checkstyle')

    def test_check_dependencies_with_checkstyle_and_java_found(self):
        """Testing CheckstyleTool.check_dependencies with configured
        checkstyle_path and java found on filesystem
        """
        self.spy_on(is_exe_in_path, op=kgb.SpyOpReturn(True))

        with self.override_config({'checkstyle_path': '/path/to/checkstyle'}):
            tool = CheckstyleTool()
            self.assertTrue(tool.check_dependencies())
            self.assertSpyCalledWith(is_exe_in_path, '/path/to/checkstyle')
            self.assertSpyCalledWith(is_exe_in_path, 'java')
