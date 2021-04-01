"""Unit tests for reviewbot.tools.base.registry."""

from __future__ import unicode_literals

import re

from reviewbot.testing import TestCase
from reviewbot.tools.base import BaseTool
from reviewbot.tools.base.registry import (_registered_tools,
                                           get_tool_class,
                                           get_tool_classes,
                                           load_tool_classes,
                                           register_tool_class,
                                           unregister_tool_class)


class RegistryTestCase(TestCase):
    """Unit tests for reviewbot.tools.base.registry."""

    def setUp(self):
        super(RegistryTestCase, self).setUp()

        _registered_tools.clear()

    @classmethod
    def tearDownClass(cls):
        super(RegistryTestCase, cls).tearDownClass()

        # Re-load all standard tools, for any other unit tests that need them.
        load_tool_classes()

    def test_register_tool_class(self):
        """Testing register_tool_class"""
        class DummyTool(BaseTool):
            tool_id = 'dummy'

        register_tool_class(DummyTool)

        self.assertEqual(
            _registered_tools,
            {
                'dummy': DummyTool,
            })

    def test_register_tool_class_with_no_tool_id(self):
        """Testing register_tool_class with no tool ID"""
        class DummyTool(BaseTool):
            pass

        expected_message = re.escape(
            'The tool class %r is missing a tool_id attribute.'
            % DummyTool
        )

        with self.assertRaisesRegexp(ValueError, expected_message):
            register_tool_class(DummyTool)

        self.assertEqual(_registered_tools, {})

    def test_register_tool_class_with_tool_id_conflict(self):
        """Testing register_tool_class with tool ID conflict"""
        class DummyTool(BaseTool):
            tool_id = 'dummy'

        class DummyTool2(BaseTool):
            tool_id = 'dummy'

        register_tool_class(DummyTool)

        expected_message = re.escape(
            'Another tool with the ID "dummy" is already registered (%r).'
            % DummyTool
        )

        with self.assertRaisesRegexp(ValueError, expected_message):
            register_tool_class(DummyTool2)

        self.assertEqual(
            _registered_tools,
            {
                'dummy': DummyTool,
            })

    def test_unregister_tool_class(self):
        """Testing unregister_tool_class"""
        class DummyTool(BaseTool):
            tool_id = 'dummy'

        _registered_tools['dummy'] = DummyTool
        unregister_tool_class('dummy')

        self.assertEqual(_registered_tools, {})

    def test_unregister_tool_class_with_not_found(self):
        """Testing unregister_tool_class with tool ID not found"""
        expected_message = re.escape(
            'A tool with the ID "dummy" was not registered.'
        )

        with self.assertRaisesRegexp(KeyError, expected_message):
            unregister_tool_class('dummy')

        self.assertEqual(_registered_tools, {})

    def test_get_tool_class(self):
        """Testing get_tool_class"""
        class DummyTool(BaseTool):
            tool_id = 'dummy'

        register_tool_class(DummyTool)

        self.assertIs(get_tool_class('dummy'), DummyTool)

    def test_get_tool_class_with_not_found(self):
        """Testing get_tool_class with tool ID not found"""
        self.assertIsNone(get_tool_class('dummy'))

    def test_get_tool_classes(self):
        """Testing get_tool_classes"""
        class DummyTool1(BaseTool):
            tool_id = 'dummy1'

        class DummyTool2(BaseTool):
            tool_id = 'dummy2'

        class DummyTool3(BaseTool):
            tool_id = 'dummy3'

        register_tool_class(DummyTool2)
        register_tool_class(DummyTool1)
        register_tool_class(DummyTool3)

        self.assertEqual(list(get_tool_classes()),
                         [DummyTool1, DummyTool2, DummyTool3])

    def test_load_tool_classes(self):
        """Testing load_tool_classes"""
        load_tool_classes()

        # Just check a few of them.
        self.assertIn('flake8', _registered_tools)
        self.assertIn('jshint', _registered_tools)
        self.assertIn('gofmt', _registered_tools)
