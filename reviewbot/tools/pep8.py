from reviewbot.tools.process import execute


def pep8Tool(file):
    print "checking: %s" % file.file_path
    if file.dest_file.endswith('.py'):
        output = execute(['pep8', '-r', (file.file_path)],
                split_lines=True,
                ignore_errors=True)

        for line in output:
            parsed = line.split(':')
            lnum = int(parsed[1])
            col = int(parsed[2])
            msg = parsed[3]
            file.comment(lnum, 1, 'Col: %s\n%s' % (col, msg), issue=False)
