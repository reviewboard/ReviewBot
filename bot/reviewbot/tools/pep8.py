from __future__ import unicode_literals

from reviewbot.tools import Tool
from reviewbot.tools.process import execute
from reviewbot.utils import is_exe_in_path


class PEP8Tool(Tool):
    name = 'PEP8 Style Checker'
    version = '0.2'
    description = "Checks code for style errors using the PEP8 tool."
    options = [
        {
            'name': 'max_line_length',
            'field_type': 'django.forms.IntegerField',
            'default': 79,
            'field_options': {
                'label': 'Maximum Line Length',
                'help_text': 'The maximum line length PEP8 will check for.',
                'required': True,
            },
        },
        {
            'name': 'ignore',
            'field_type': 'django.forms.CharField',
            'default': "",
            'field_options': {
                'label': 'Ignore',
                'help_text': 'A comma seperated list of errors and warnings '
                             'to ignore. This will be passed to the --ignore '
                             'command line argument (e.g. E4,W).',
                'required': False,
            },
        },
    ]

    def check_dependencies(self):
        return is_exe_in_path('pep8')

    def handle_file(self, f):
        if not f.dest_file.endswith('.py'):
            # Ignore the file.
            return False

        path = f.get_patched_file_path()
        if not path:
            return False

        output = execute(
            [
                'pep8',
                '-r',
                '--max-line-length=%i' % self.settings['max_line_length'],
                '--ignore=%s' % self.settings['ignore'],
                path
            ],
            split_lines=True,
            ignore_errors=True)

        for line in output:
            parsed = line.split(':', 3)
            lnum = int(parsed[1])
            col = int(parsed[2])
            msg = parsed[3]
            f.comment('Col: %s\n%s' % (col, msg), lnum)

        return True
