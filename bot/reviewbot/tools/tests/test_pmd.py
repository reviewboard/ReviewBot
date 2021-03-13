"""Unit tests for reviewbot.tools.pmd."""

from __future__ import unicode_literals

import kgb

from reviewbot.testing import TestCase
from reviewbot.tools.pmd import PMDTool
from reviewbot.utils.process import is_exe_in_path


class PMDToolTests(kgb.SpyAgency, TestCase):
    """Unit tests for reviewbot.tools.pmd.PMDTool."""

    def test_check_dependencies_with_no_config(self):
        """Testing PMDTool.check_dependencies with no configured pmd_path"""
        with self.override_config({}):
            tool = PMDTool()
            self.assertFalse(tool.check_dependencies())

    def test_check_dependencies_with_pmd_not_found(self):
        """Testing PMDTool.check_dependencies with configured pmd_path not
        found on filesystem
        """
        self.spy_on(is_exe_in_path, op=kgb.SpyOpReturn(False))

        with self.override_config({'pmd_path': '/path/to/pmd'}):
            tool = PMDTool()
            self.assertFalse(tool.check_dependencies())
            self.assertSpyCalledWith(is_exe_in_path, '/path/to/pmd')

    def test_check_dependencies_with_pmd_found(self):
        """Testing PMDTool.check_dependencies with configured pmd_path
        found on filesystem
        """
        self.spy_on(is_exe_in_path, op=kgb.SpyOpReturn(True))

        with self.override_config({'pmd_path': '/path/to/pmd'}):
            tool = PMDTool()
            self.assertTrue(tool.check_dependencies())
            self.assertSpyCalledWith(is_exe_in_path, '/path/to/pmd')
