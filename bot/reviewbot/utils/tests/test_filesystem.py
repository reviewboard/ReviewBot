"""Unit tests for reviewbot.utils.filesystem.

Version Added:
    3.0
"""

from __future__ import unicode_literals

from reviewbot.errors import SuspiciousFilePath
from reviewbot.testing import TestCase
from reviewbot.utils.filesystem import (PathPlatform,
                                        get_path_platform,
                                        normalize_platform_path)


class GetPathPlatformTests(TestCase):
    """Unit tests for reviewbot.utils.filesystem.get_path_platform."""

    def test_with_windows_abs(self):
        """Testing get_path_platform with absolute Windows path"""
        self.assertEqual(get_path_platform(r'C:\Documents\Test'),
                         PathPlatform.WINDOWS)

    def test_with_windows_rel(self):
        """Testing get_path_platform with relative Windows path"""
        self.assertEqual(get_path_platform(r'Documents\Test'),
                         PathPlatform.WINDOWS)
        self.assertEqual(get_path_platform(r'.\Documents\Test'),
                         PathPlatform.WINDOWS)
        self.assertEqual(get_path_platform(r'Documents\..\Test'),
                         PathPlatform.WINDOWS)

    def test_with_windows_unc(self):
        """Testing get_path_platform with Windows-style UNC path"""
        self.assertEqual(get_path_platform(r'\\host\computer\Documents\Tests'),
                         PathPlatform.WINDOWS)

    def test_with_posix_abs(self):
        """Testing get_path_platform with absolute POSIX path"""
        self.assertEqual(get_path_platform('/documents/test'),
                         PathPlatform.POSIX)

    def test_with_posix_rel(self):
        """Testing get_path_platform with relative POSIX path"""
        self.assertEqual(get_path_platform('documents/test'),
                         PathPlatform.POSIX)
        self.assertEqual(get_path_platform('./documents/test'),
                         PathPlatform.POSIX)
        self.assertEqual(get_path_platform('documents/../test'),
                         PathPlatform.POSIX)

    def test_with_posix_unc(self):
        """Testing get_path_platform with POSIX-style UNC path"""
        self.assertEqual(get_path_platform('//host/computer/documents/tests'),
                         PathPlatform.POSIX)

    def test_with_bare(self):
        """Testing get_path_platform with bare filename"""
        self.assertEqual(get_path_platform('test'),
                         PathPlatform.POSIX)


class NormalizePlatformPath(TestCase):
    """Unit tests for reviewbot.utils.filesystem.normalize_platform_path."""

    def test_with_windows_abs(self):
        """Testing normalize_platform_path with absolute Windows path"""
        self._test_path(r'C:\Documents\Tests',
                        expected_posix_path='Documents/Tests',
                        expected_windows_path=r'Documents\Tests')
        self._test_path(r'C:\Documents\..\..\..\..\Tests',
                        expected_posix_path='Tests',
                        expected_windows_path='Tests')

    def test_with_windows_abs_and_relative_to(self):
        """Testing normalize_platform_path with absolute Windows path and
        relative_to=
        """
        self._test_path(r'C:\Documents\Tests',
                        relative_to_posix='/src/test',
                        relative_to_windows=r'C:\src\test',
                        expected_posix_path='/src/test/Documents/Tests',
                        expected_windows_path=r'C:\src\test\Documents\Tests')
        self._test_path(r'C:\Documents\..\..\..\Tests',
                        relative_to_posix='/src/test',
                        relative_to_windows=r'C:\src\test',
                        expected_posix_path='/src/test/Tests',
                        expected_windows_path=r'C:\src\test\Tests')

    def test_with_windows_rel(self):
        """Testing normalize_platform_path with relative Windows path"""
        self._test_path(r'Documents\Tests',
                        expected_posix_path='Documents/Tests',
                        expected_windows_path=r'Documents\Tests')
        self._test_path(r'.\Documents\Tests',
                        expected_posix_path='Documents/Tests',
                        expected_windows_path=r'Documents\Tests')
        self._test_path(r'Documents\..\Tests',
                        expected_posix_path='Tests',
                        expected_windows_path='Tests')

    def test_with_windows_rel_and_relative_to(self):
        """Testing normalize_platform_path with relative Windows path and
        relative_to=
        """
        self._test_path(r'Documents\Tests',
                        relative_to_posix='/src/test',
                        relative_to_windows=r'C:\src\test',
                        expected_posix_path='/src/test/Documents/Tests',
                        expected_windows_path=r'C:\src\test\Documents\Tests')
        self._test_path(r'.\Documents\Tests',
                        relative_to_posix='/src/test',
                        relative_to_windows=r'C:\src\test',
                        expected_posix_path='/src/test/Documents/Tests',
                        expected_windows_path=r'C:\src\test\Documents\Tests')

    def test_with_windows_rel_and_suspicious_path(self):
        """Testing normalize_platform_path with suspicious relative Windows
        path
        """
        with self.assertRaises(SuspiciousFilePath):
            self._test_path(r'Documents\..\..\..\Tests',
                            expected_posix_path='Tests',
                            expected_windows_path='Tests')

    def test_with_windows_unc(self):
        """Testing normalize_platform_path with Windows-style UNC path"""
        self._test_path(r'\\host\computer\Documents\Tests',
                        expected_posix_path='Documents/Tests',
                        expected_windows_path=r'Documents\Tests')

    def test_with_windows_unc_and_relative_to(self):
        """Testing normalize_platform_path with Windows-style UNC path and
        relative_to=
        """
        self._test_path(r'\\host\computer\Documents\Tests',
                        relative_to_posix='/src/test',
                        relative_to_windows=r'C:\src\test',
                        expected_posix_path='/src/test/Documents/Tests',
                        expected_windows_path=r'C:\src\test\Documents\Tests')

    def test_with_posix_abs(self):
        """Testing normalize_platform_path with absolute POSIX path"""
        self._test_path('/documents/tests',
                        expected_posix_path='documents/tests',
                        expected_windows_path=r'documents\tests')
        self._test_path('/documents/../../../tests',
                        expected_posix_path='tests',
                        expected_windows_path='tests')

    def test_with_posix_abs_and_relative_to(self):
        """Testing normalize_platform_path with absolute POSIX path and
        relative_to
        """
        self._test_path('/documents/tests',
                        relative_to_posix='/src/test',
                        relative_to_windows=r'C:\src\test',
                        expected_posix_path='/src/test/documents/tests',
                        expected_windows_path=r'C:\src\test\documents\tests')
        self._test_path('/documents/../../../tests',
                        relative_to_posix='/src/test',
                        relative_to_windows=r'C:\src\test',
                        expected_posix_path='/src/test/tests',
                        expected_windows_path=r'C:\src\test\tests')

    def test_with_posix_rel(self):
        """Testing normalize_platform_path with relative POSIX path"""
        self._test_path('documents/tests',
                        expected_posix_path='documents/tests',
                        expected_windows_path=r'documents\tests')
        self._test_path('./documents/tests',
                        expected_posix_path='documents/tests',
                        expected_windows_path=r'documents\tests')
        self._test_path('documents/../tests',
                        expected_posix_path='tests',
                        expected_windows_path='tests')

    def test_with_posix_rel_and_relative_to(self):
        """Testing normalize_platform_path with relative POSIX path and
        relative_to=
        """
        self._test_path('documents/tests',
                        relative_to_posix='/src/test',
                        relative_to_windows=r'C:\src\test',
                        expected_posix_path='/src/test/documents/tests',
                        expected_windows_path=r'C:\src\test\documents\tests')
        self._test_path('./documents/tests',
                        relative_to_posix='/src/test',
                        relative_to_windows=r'C:\src\test',
                        expected_posix_path='/src/test/documents/tests',
                        expected_windows_path=r'C:\src\test\documents\tests')
        self._test_path('documents/../tests',
                        relative_to_posix='/src/test',
                        relative_to_windows=r'C:\src\test',
                        expected_posix_path='/src/test/tests',
                        expected_windows_path=r'C:\src\test\tests')

    def test_with_posix_rel_and_suspicious_path(self):
        """Testing normalize_platform_path with suspicious relative POSIX path
        """
        with self.assertRaises(SuspiciousFilePath):
            self._test_path('documents/../../../tests',
                            expected_posix_path='/src/test/tests',
                            expected_windows_path=r'C:\src\test\tests')

    def test_with_posix_unc(self):
        """Testing normalize_platform_path with POSIX-style UNC path"""
        self._test_path('//host/computer/documents/tests',
                        expected_posix_path='documents/tests',
                        expected_windows_path=r'documents\tests')

    def test_with_posix_unc_and_relative_to(self):
        """Testing normalize_platform_path with POSIX-style UNC path and
        relative_to=
        """
        self._test_path('//host/computer/documents/tests',
                        relative_to_posix='/src/test',
                        relative_to_windows=r'C:\src\test',
                        expected_posix_path='/src/test/documents/tests',
                        expected_windows_path=r'C:\src\test\documents\tests')

    def test_with_bare(self):
        """Testing normalize_platform_path with bare filename"""
        self._test_path('tests.txt',
                        expected_posix_path='tests.txt',
                        expected_windows_path='tests.txt')

    def test_with_bare_and_relative_to(self):
        """Testing normalize_platform_path with bare filename and relative_to=
        """
        self._test_path('tests.txt',
                        relative_to_posix='/src/test',
                        relative_to_windows=r'C:\src\test',
                        expected_posix_path='/src/test/tests.txt',
                        expected_windows_path=r'C:\src\test\tests.txt')

    def _test_path(self, path, expected_posix_path, expected_windows_path,
                   relative_to_posix=None, relative_to_windows=None):
        """Test path normalization against Windows and POSIX paths.

        This will test that a path normalizes correctly on both Windows and
        Linux, with or without relative paths.

        Args:
            path (unicode):
                The path to normalize.

            expected_posix_path (unicode):
                The expected resulting POSIX path.

            expected_windows_path (unicode):
                The expected resulting Windows path.

            relative_to_posix (unicode, optional):
                An optional path to prepend to the normalized POSIX path.

            relative_to_windows (unicode, optional):
                An optional path to prepend to the normalized Windows path.

        Raises:
            AssertionError:
                A normalized path did not equal the expected result.
        """
        self.assertEqual(
            normalize_platform_path(path,
                                    relative_to=relative_to_posix,
                                    target_platform=PathPlatform.POSIX),
            expected_posix_path)
        self.assertEqual(
            normalize_platform_path(path,
                                    relative_to=relative_to_windows,
                                    target_platform=PathPlatform.WINDOWS),
            expected_windows_path)
