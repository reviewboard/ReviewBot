from reviewbot.tools.process import execute
from reviewbot.tools import Tool


class pep8Tool(Tool):
    key = 'pep8'
    name = 'PEP8 Style Checker'
    version = '0.1'

    def handle_file(self, f):
        if not f.dest_file.endswith('.py'):
            # Ignore the file.
            return False

        path = f.get_patched_file_path()
        if not path:
            return False

        output = execute(['pep8', '-r', path],
                split_lines=True,
                ignore_errors=True)

        for line in output:
            parsed = line.split(':')
            lnum = int(parsed[1])
            col = int(parsed[2])
            msg = parsed[3]
            f.comment('Col: %s\n%s' % (col, msg), lnum)

        return True
