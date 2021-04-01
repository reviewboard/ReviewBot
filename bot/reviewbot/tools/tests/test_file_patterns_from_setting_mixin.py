"""Unit tests for reviewbot.tools.base.mixins.FilePatternFromSettingMixin."""

from __future__ import unicode_literals

from reviewbot.testing import TestCase
from reviewbot.tools.base.mixins import FilePatternsFromSettingMixin
from reviewbot.tools.base.tool import BaseTool


class FilePatternsFromSettingMixinTests(TestCase):
    """Unit tests for reviewbot.tools.base.mixins.FilePatternFromSettingMixin.
    """

    def test_file_extensions_settings(self):
        """Testing FilePatternsFromSettingMixin with file_extensions_setting"""
        class MyTool(FilePatternsFromSettingMixin, BaseTool):
            file_extensions_setting = 'extensions'
            file_patterns = ['*.java']

        tool = MyTool(settings={
            'extensions': '.py,txt,, c, .c',
        })

        self.assertEqual(tool.file_patterns,
                         ['*.c', '*.java', '*.py', '*.txt'])

    def test_file_extensions_settings_with_include_default_false(self):
        """Testing FilePatternsFromSettingMixin with file_extensions_setting
        and include_default_file_patterns=False
        """
        class MyTool(FilePatternsFromSettingMixin, BaseTool):
            file_extensions_setting = 'extensions'
            file_patterns_setting = 'patterns'
            file_patterns = ['*.java']
            include_default_file_patterns = False

        tool = MyTool(settings={
            'extensions': '.py,txt,, c, .c',
            'patterns': '',
        })

        self.assertEqual(tool.file_patterns, ['*.c', '*.py', '*.txt'])

    def test_file_extensions_settings_escaping(self):
        """Testing FilePatternsFromSettingMixin with file_extensions_setting
        value escaped
        """
        class MyTool(FilePatternsFromSettingMixin, BaseTool):
            file_extensions_setting = 'extensions'

        tool = MyTool(settings={
            'extensions': '.ext*,ext?,.ext[,.ext]',
        })

        self.assertEqual(tool.file_patterns,
                         ['*.ext[*]', '*.ext[?]', '*.ext[[]', '*.ext]'])

    def test_file_patterns_settings(self):
        """Testing FilePatternsFromSettingMixin with file_patterns_setting"""
        class MyTool(FilePatternsFromSettingMixin, BaseTool):
            file_extensions_setting = 'extensions'
            file_patterns_setting = 'patterns'
            file_patterns = ['*.java']

        # We include "extensions" for precedence checking.
        tool = MyTool(settings={
            'patterns': '.*.py,, *.c*',
            'extensions': '.xxx',
        })

        self.assertEqual(tool.file_patterns, ['*.c*', '*.java', '.*.py'])

    def test_file_patterns_settings_with_include_default_false(self):
        """Testing FilePatternsFromSettingMixin with file_patterns_setting and
        include_default_file_patterns=False
        """
        class MyTool(FilePatternsFromSettingMixin, BaseTool):
            file_extensions_setting = 'extensions'
            file_patterns_setting = 'patterns'
            file_patterns = ['*.java']
            include_default_file_patterns = False

        # We include "extensions" for precedence checking.
        tool = MyTool(settings={
            'patterns': '.*.py,, *.c*',
            'extensions': '.bak',
        })

        self.assertEqual(tool.file_patterns, ['*.c*', '.*.py'])

    def test_no_settings_provided(self):
        """Testing FilePatternsFromSettingMixin with no settings provided
        in configuration
        """
        class MyTool(FilePatternsFromSettingMixin, BaseTool):
            file_extensions_setting = 'extensions'
            file_patterns_setting = 'patterns'
            file_patterns = ['*.java']

        tool = MyTool(settings={
            'extensions': '',
        })

        self.assertEqual(tool.file_patterns, ['*.java'])

    def test_no_settings_provided_and_include_default_false(self):
        """Testing FilePatternsFromSettingMixin with no settings provided
        in configuration and include_default_file_patterns=False
        """
        class MyTool(FilePatternsFromSettingMixin, BaseTool):
            file_extensions_setting = 'extensions'
            file_patterns_setting = 'patterns'
            file_patterns = ['*.java']
            include_default_file_patterns = False

        tool = MyTool(settings={
            'extensions': '',
        })

        self.assertEqual(tool.file_patterns, ['*.java'])
