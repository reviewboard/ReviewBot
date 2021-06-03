"""Unit tests for reviewbot.utils.text."""

from __future__ import unicode_literals

from reviewbot.testing import TestCase
from reviewbot.utils.text import split_comma_separated


class SplitCommaSeparatedTests(TestCase):
    """Unit tests for reviewbot.utils.text.split_comma_separated."""

    def test_with_blank(self):
        """Testing split_comma_separated with blank string"""
        self.assertEqual(split_comma_separated(''), [])

    def test_with_values(self):
        """Testing split_comma_separated with multiple values"""
        self.assertEqual(split_comma_separated('a,b,c'), ['a', 'b', 'c'])

    def test_with_single_values(self):
        """Testing split_comma_separated with single value"""
        self.assertEqual(split_comma_separated('a'), ['a'])

    def test_with_extra_garbage(self):
        """Testing split_comma_separated with extra spaces and commas"""
        self.assertEqual(split_comma_separated(' ,, a,b, c ,,'),
                         ['a', 'b', 'c'])

    def test_with_only_garbage(self):
        """Testing split_comma_separated with extra spaces and commas"""
        self.assertEqual(split_comma_separated(' ,, ,  ,,,'), [])
