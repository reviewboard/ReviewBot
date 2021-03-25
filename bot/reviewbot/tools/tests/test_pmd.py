"""Unit tests for reviewbot.tools.pmd."""

from __future__ import unicode_literals

import os

import kgb

from reviewbot.testing import TestCase
from reviewbot.tools.pmd import PMDTool
from reviewbot.utils.process import execute, is_exe_in_path


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

        new_config = {
            'exe_paths': {
                'pmd': '/path/to/pmd',
            }
        }

        with self.override_config(new_config):
            tool = PMDTool()
            self.assertFalse(tool.check_dependencies())
            self.assertSpyCalledWith(is_exe_in_path, '/path/to/pmd')

    def test_check_dependencies_with_pmd_found(self):
        """Testing PMDTool.check_dependencies with configured pmd_path
        found on filesystem
        """
        self.spy_on(is_exe_in_path, op=kgb.SpyOpReturn(True))

        new_config = {
            'exe_paths': {
                'pmd': '/path/to/pmd',
            }
        }

        with self.override_config(new_config):
            tool = PMDTool()
            self.assertTrue(tool.check_dependencies())
            self.assertSpyCalledWith(is_exe_in_path, '/path/to/pmd')

    def test_handle_file_with_ruleset_names(self):
        """Testing PMDTool.handle_file with ruleset names"""
        @self.spy_for(execute)
        def _execute(cmdline, **kwargs):
            self.assertEqual(len(cmdline), 10)
            self.assertEqual(
                cmdline[:3],
                [
                    '/path/to/pmd',
                    'pmd',
                    '-d',
                ])
            self.assertEqual(
                cmdline[4:-1],
                [
                    '-R', 'ruleset1,ruleset2',
                    '-f', 'csv',
                    '-r',
                ])

            patch_filename = cmdline[3]
            output_filename = cmdline[9]

            self.assertTrue(os.path.exists(patch_filename))
            self.assertTrue(os.path.exists(output_filename))

            with open(output_filename, 'w') as fp:
                fp.write(
                    '"Problem","Package","File","Priority","Line",'
                    '"Description","Rule set","Rule",\n'
                )
                fp.write(
                    '"1","some.package","%s","1","12","Something is wrong '
                    'here","ruleset1","rule1"\n'
                    % patch_filename
                )
                fp.write(
                    '"1","some.package","%s","1","48","And another thing",'
                    '"ruleset2","rule2"\n'
                    % patch_filename
                )

        review, review_file = self._run_handle_file(settings={
            'file_ext': '',
            'rulesets': 'ruleset1,ruleset2',
        })

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 12,
                'num_lines': 1,
                'text': 'Something is wrong here',
                'issue_opened': True,
                'rich_text': False,
            },
            {
                'filediff_id': review_file.id,
                'first_line': 41,
                'num_lines': 1,
                'text': 'And another thing',
                'issue_opened': True,
                'rich_text': False,
            },
        ])
        self.assertEqual(review.general_comments, [])

    def test_handle_file_with_ruleset_xml(self):
        """Testing PMDTool.handle_file with ruleset configuration XML"""
        @self.spy_for(execute)
        def _execute(cmdline, **kwargs):
            self.assertEqual(len(cmdline), 10)
            self.assertEqual(
                cmdline[:3],
                [
                    '/path/to/pmd',
                    'pmd',
                    '-d',
                ])
            self.assertEqual(cmdline[4], '-R')
            self.assertEqual(
                cmdline[6:-1],
                [
                    '-f', 'csv',
                    '-r',
                ])

            patch_filename = cmdline[3]
            ruleset_filename = cmdline[5]
            output_filename = cmdline[9]

            self.assertTrue(os.path.exists(patch_filename))
            self.assertTrue(os.path.exists(ruleset_filename))
            self.assertTrue(os.path.exists(output_filename))

            with open(ruleset_filename, 'r') as fp:
                self.assertEqual(fp.read(), ruleset_xml)

            with open(output_filename, 'w') as fp:
                fp.write(
                    '"Problem","Package","File","Priority","Line",'
                    '"Description","Rule set","Rule",\n'
                )
                fp.write(
                    '"1","some.package","%s","1","12","Something is wrong '
                    'here","ruleset1","rule1"\n'
                    % patch_filename
                )
                fp.write(
                    '"1","some.package","%s","1","48","And another thing",'
                    '"ruleset2","rule2"\n'
                    % patch_filename
                )

        # Note that this is not a valid ruleset XML, but we don't need it
        # to be for the test.
        ruleset_xml = (
            '<?xml version="1.0"?>\n'
            '<ruleset name="My Ruleset" />\n'
        )

        review, review_file = self._run_handle_file(settings={
            'file_ext': '',
            'rulesets': ruleset_xml,
        })

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 12,
                'num_lines': 1,
                'text': 'Something is wrong here',
                'issue_opened': True,
                'rich_text': False,
            },
            {
                'filediff_id': review_file.id,
                'first_line': 41,
                'num_lines': 1,
                'text': 'And another thing',
                'issue_opened': True,
                'rich_text': False,
            },
        ])
        self.assertEqual(review.general_comments, [])

    def test_handle_file_with_file_ext_match(self):
        """Testing PMDTool.handle_file when file_ext matches"""
        self.spy_on(execute, call_original=False)

        self._run_handle_file(settings={
            'file_ext': 'c,py',
            'rulesets': 'ruleset1',
        })

        self.assertSpyCalled(execute)

    def test_handle_file_with_file_ext_match_variants(self):
        """Testing PMDTool.handle_file when file_ext matches with variations
        in file extension configuration
        """
        self.spy_on(execute, call_original=False)

        self._run_handle_file(settings={
            'file_ext': 'c,, .py',
            'rulesets': 'ruleset1',
        })

        self.assertSpyCalled(execute)

    def test_handle_file_without_file_ext_match(self):
        """Testing PMDTool.handle_file when file_ext doesn't match"""
        self.spy_on(execute, call_original=False)

        self._run_handle_file(settings={
            'file_ext': 'txt,pyxyz',
            'rulesets': 'ruleset1',
        })

        self.assertSpyNotCalled(execute)

    def _run_handle_file(self, settings):
        """Set up and run a handle_file test.

        This will create the review objects, configure the path to PMD, and
        run the test.

        Args:
            settings (dict):
                The settings to pass to
                :py:meth:`~reviewbot.tools.pmd.PMDTool.handle_file`.

        Returns:
            tuple:
            A tuple containing the review and the file.
        """
        review = self.create_review()
        review_file = self.create_review_file(
            review,
            source_file='test.py',
            dest_file='test.py',
            diff_data=self.create_diff_data(chunks=[
                {
                    'change': 'insert',
                    'lines': ['import foo'],
                    'new_linenum': 12,
                    'old_linenum': 11,
                },
                {
                    'change': 'replace',
                    'lines': [
                        ('except Exception:',
                         'except Exception as e:'),
                    ],
                    'new_linenum': 48,
                    'old_linenum': 40,
                },
            ]))

        new_config = {
            'exe_paths': {
                'pmd': '/path/to/pmd',
            }
        }

        with self.override_config(new_config):
            tool = PMDTool(settings=settings)
            tool.handle_files([review_file])

        return review, review_file
