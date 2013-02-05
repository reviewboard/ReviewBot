from reviewbot.tools import Tool
from reviewbot.tools.process import execute
from reviewbot.utils import is_exe_in_path


class PyflakesTool(Tool):
    name = 'Pyflakes'
    version = '0.1'
    description = "Checks Python code for errors using Pyflakes."

    def check_dependencies(self):
        return is_exe_in_path('pyflakes')

    def handle_file(self, f):
        if not f.dest_file.endswith('.py'):
            # Ignore the file.
            return False

        path = f.get_patched_file_path()
        if not path:
            return False

        output = execute(
            [
                'pyflakes',
                path
            ],
            split_lines=True,
            ignore_errors=True)

        for line in output:
            parsed = line.split(':', 2)
            lnum = int(parsed[1])
            msg = parsed[2]
            f.comment('%s' % (msg, ), lnum)

        return True
