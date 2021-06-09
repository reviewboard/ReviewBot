"""Unit tests for reviewbot.tools.checkstyle."""

from __future__ import unicode_literals

import os

import kgb
import six

from reviewbot.config import config
from reviewbot.testing import get_test_dep_path
from reviewbot.tools.checkstyle import CheckstyleTool
from reviewbot.tools.testing import (BaseToolTestCase,
                                     ToolTestCaseMetaclass,
                                     integration_test,
                                     simulation_test)
from reviewbot.utils.filesystem import tmpdirs, tmpfiles
from reviewbot.utils.process import execute


@six.add_metaclass(ToolTestCaseMetaclass)
class CheckstyleToolTests(BaseToolTestCase):
    """Unit tests for reviewbot.tools.checkstyle.CheckstyleTool."""

    tool_class = CheckstyleTool
    tool_exe_config_key = 'java'
    tool_exe_path = '/path/to/java'

    config = {
        'java_classpaths': {
            'checkstyle': [
                get_test_dep_path('checkstyle.jar'),
            ],
        },
    }

    SAMPLE_JAVA_CODE = (
        b'public class Test {\n'
        b'  void Test_Func() {\n'
        b'  }\n'
        b'}\n'
    )

    @integration_test()
    @simulation_test(output=(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<checkstyle version="8.41.1">\n'
        ' <file name="/Test.java">\n'
        '  <error line="1" column="1" severity="warning"\n'
        '         message="Missing a Javadoc comment."\n'
        '         source="com.puppycrawl.tools.checkstyle.checks.'
        'javadoc.MissingJavadocTypeCheck"/>\n'
        '  <error line="2" column="8" severity="warning"\n'
        '         message="Method name &apos;Test_Func&apos; must match '
        'pattern &apos;^[a-z][a-z0-9][a-zA-Z0-9_]*$&apos;."\n'
        '         source="com.puppycrawl.tools.checkstyle.checks.naming.'
        'MethodNameCheck"/>\n'
        ' </file>\n'
        '</checkstyle>'
    ))
    def test_execute_with_google_checks_xml(self):
        """Testing CheckstyleTool.execute with config=google_checks.xml"""
        review, review_file = self.run_tool_execute(
            filename='Test.java',
            file_contents=self.SAMPLE_JAVA_CODE,
            tool_settings={
                'config': 'google_checks.xml',
            })

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 1,
                'num_lines': 1,
                'text': (
                    'Missing a Javadoc comment.\n'
                    '\n'
                    'Column: 1\n'
                    'Severity: warning\n'
                    'Error code: com.puppycrawl.tools.checkstyle.checks.'
                    'javadoc.MissingJavadocTypeCheck'
                ),
                'issue_opened': True,
                'rich_text': False,
            },
            {
                'filediff_id': review_file.id,
                'first_line': 2,
                'num_lines': 1,
                'text': (
                    "Method name 'Test_Func' must match pattern "
                    "'^[a-z][a-z0-9][a-zA-Z0-9_]*$'.\n"
                    "\n"
                    "Column: 8\n"
                    "Severity: warning\n"
                    "Error code: com.puppycrawl.tools.checkstyle.checks."
                    "naming.MethodNameCheck"
                ),
                'issue_opened': True,
                'rich_text': False,
            },
        ])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                '-cp', config['java_classpaths']['checkstyle'][0],
                'com.puppycrawl.tools.checkstyle.Main',
                '-f=xml',
                '-c=google_checks.xml',
                os.path.join(tmpdirs[-1], 'Test.java'),
            ],
            ignore_errors=True)

    @integration_test()
    @simulation_test(output=(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<checkstyle version="8.41.1">\n'
        ' <file name="/Test.java">\n'
        '  <error line="1" severity="error"\n'
        '         message="Missing package-info.java file."\n'
        '         source="com.puppycrawl.tools.checkstyle.checks.javadoc.'
        'JavadocPackageCheck"/>\n'
        '  <error line="2" column="8" severity="error"\n'
        '         message="Name &apos;Test_Func&apos; must match pattern '
        '&apos;^[a-z][a-zA-Z0-9]*$&apos;."\n'
        '         source="com.puppycrawl.tools.checkstyle.checks.naming.'
        'MethodNameCheck"/>\n'
        ' </file>\n'
        '</checkstyle>'
    ))
    def test_execute_with_sun_checks_xml(self):
        """Testing CheckstyleTool.execute with config=sun_checks.xml"""
        review, review_file = self.run_tool_execute(
            filename='Test.java',
            file_contents=self.SAMPLE_JAVA_CODE,
            tool_settings={
                'config': 'sun_checks.xml',
            })

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 1,
                'num_lines': 1,
                'text': (
                    'Missing package-info.java file.\n'
                    '\n'
                    'Severity: error\n'
                    'Error code: com.puppycrawl.tools.checkstyle.checks.'
                    'javadoc.JavadocPackageCheck'
                ),
                'issue_opened': True,
                'rich_text': False,
            },
            {
                'filediff_id': review_file.id,
                'first_line': 2,
                'num_lines': 1,
                'text': (
                    "Name 'Test_Func' must match pattern "
                    "'^[a-z][a-zA-Z0-9]*$'.\n"
                    "\n"
                    "Column: 8\n"
                    "Severity: error\n"
                    "Error code: com.puppycrawl.tools.checkstyle.checks."
                    "naming.MethodNameCheck"
                ),
                'issue_opened': True,
                'rich_text': False,
            },
        ])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                '-cp', config['java_classpaths']['checkstyle'][0],
                'com.puppycrawl.tools.checkstyle.Main',
                '-f=xml',
                '-c=sun_checks.xml',
                os.path.join(tmpdirs[-1], 'Test.java'),
            ],
            ignore_errors=True)

    @integration_test()
    @simulation_test(output=(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<checkstyle version="8.41.1">\n'
        ' <file name="/Test.java">\n'
        '  <error line="2" column="8" severity="error"\n'
        '         message="The method &quot;Test_Func&quot; must be in '
        'snake_case format."\n'
        '         source="com.puppycrawl.tools.checkstyle.checks.naming.'
        'MethodNameCheck"/>\n'
        ' </file>\n'
        '</checkstyle>'
    ))
    def test_execute_with_custom_config(self):
        """Testing CheckstyleTool.execute with custom config="""
        review, review_file = self.run_tool_execute(
            filename='Test.java',
            file_contents=self.SAMPLE_JAVA_CODE,
            tool_settings={
                'config': (
                    '<?xml version="1.0"?>\n'
                    '<!DOCTYPE module PUBLIC\n'
                    '  "-//Checkstyle//DTD Checkstyle Configuration 1.3//EN"\n'
                    '  "https://checkstyle.org/dtds/configuration_1_3.dtd">\n'
                    '<module name="Checker">\n'
                    '\n'
                    ' <property name="severity" value="error"/>\n'
                    ' <property name="fileExtensions" value="java"/>\n'
                    ' <module name="TreeWalker">\n'
                    '  <module name="MethodName">\n'
                    '   <property name="format" value="^[a-z][a-z0-9_]*$"/>\n'
                    '   <message key="name.invalidPattern"\n'
                    '            value="The method &quot;{0}&quot; must be in '
                    'snake_case format."/>\n'
                    '  </module>\n'
                    ' </module>\n'
                    '</module>\n'
                ),
            })

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 2,
                'num_lines': 1,
                'text': (
                    'The method "Test_Func" must be in snake_case format.\n'
                    '\n'
                    'Column: 8\n'
                    'Severity: error\n'
                    'Error code: com.puppycrawl.tools.checkstyle.checks.'
                    'naming.MethodNameCheck'
                ),
                'issue_opened': True,
                'rich_text': False,
            },
        ])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                '-cp', config['java_classpaths']['checkstyle'][0],
                'com.puppycrawl.tools.checkstyle.Main',
                '-f=xml',
                '-c=%s' % tmpfiles[-1],
                os.path.join(tmpdirs[-1], 'Test.java'),
            ],
            ignore_errors=True)

    @integration_test()
    @simulation_test(output=(
        'com.puppycrawl.tools.checkstyle.api.CheckstyleException: '
        'Exception was thrown while processing /Test.java\n'

        'exception exception...\n'
    ))
    def test_execute_with_bad_config(self):
        """Testing CheckstyleTool.execute with bad config= setting"""
        review, review_file = self.run_tool_execute(
            filename='Test.java',
            file_contents=self.SAMPLE_JAVA_CODE,
            tool_settings={
                'config': (
                    '<?xml version="1.0"?>\n'
                    '<!DOCTYPE module PUBLIC\n'
                    '  "-//Checkstyle//DTD Checkstyle Configuration 1.3//EN"\n'
                    '  "https://checkstyle.org/dtds/configuration_1_3.dtd">\n'
                    '<module name="Checker">\n'
                ),
            })

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 1,
                'num_lines': 1,
                'text': (
                    "checkstyle wasn't able to parse this file. Check the "
                    "file for syntax errors, and make sure that your "
                    "configured settings in Review Bot are correct."
                ),
                'issue_opened': True,
                'rich_text': False,
            },
        ])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                '-cp', config['java_classpaths']['checkstyle'][0],
                'com.puppycrawl.tools.checkstyle.Main',
                '-f=xml',
                '-c=%s' % tmpfiles[-1],
                os.path.join(tmpdirs[-1], 'Test.java'),
            ],
            ignore_errors=True)

    @integration_test()
    @simulation_test(output=(
        'com.puppycrawl.tools.checkstyle.api.CheckstyleException: '
        'Exception was thrown while processing /Test.java\n'

        'exception exception...\n'
    ))
    def test_execute_with_syntax_error(self):
        """Testing CheckstyleTool.execute with syntax error"""
        review, review_file = self.run_tool_execute(
            filename='Test.java',
            file_contents=(
                b'public class Test {\n'
            ),
            tool_settings={
                'config': 'google_checks.xml',
            })

        self.assertEqual(review.comments, [
            {
                'filediff_id': review_file.id,
                'first_line': 1,
                'num_lines': 1,
                'text': (
                    "checkstyle wasn't able to parse this file. Check the "
                    "file for syntax errors, and make sure that your "
                    "configured settings in Review Bot are correct."
                ),
                'issue_opened': True,
                'rich_text': False,
            },
        ])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                '-cp', config['java_classpaths']['checkstyle'][0],
                'com.puppycrawl.tools.checkstyle.Main',
                '-f=xml',
                '-c=google_checks.xml',
                os.path.join(tmpdirs[-1], 'Test.java'),
            ],
            ignore_errors=True)

    @integration_test()
    @simulation_test(output=(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        ' <checkstyle version="8.41.1">\n'
        '  <file name="/Test.java">\n'
        '  </file>\n'
        '</checkstyle>\n'
    ))
    def test_execute_with_success(self):
        """Testing CheckstyleTool.execute with successful result"""
        review, review_file = self.run_tool_execute(
            filename='Test.java',
            file_contents=(
                b'/**\n'
                b' * JavaDoc comment.\n'
                b' */\n'
                b'public class Test {\n'
                b'}\n'
            ),
            tool_settings={
                'config': 'google_checks.xml',
            })

        self.assertEqual(review.comments, [])

        self.assertSpyCalledWith(
            execute,
            [
                self.tool_exe_path,
                '-cp', config['java_classpaths']['checkstyle'][0],
                'com.puppycrawl.tools.checkstyle.Main',
                '-f=xml',
                '-c=google_checks.xml',
                os.path.join(tmpdirs[-1], 'Test.java'),
            ],
            ignore_errors=True)

    def setup_simulation_test(self, output):
        """Set up the simulation test for pycodestyle.

        This will spy on :py:func:`~reviewbot.utils.process.execute`, making
        it return the provided payload.

        Args:
            output (unicode):
                The outputted payload.
        """
        self.spy_on(execute, op=kgb.SpyOpReturn(output))
