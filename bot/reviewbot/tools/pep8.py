from reviewbot.tools.process import execute


def pep8Tool(review):

    ignored_files = []
    processed_files = []

    for file in review.files:
        if not file.dest_file.endswith('.py'):
            ignored_files.append(file.dest_file)
            continue

        processed_files.append(file.dest_file)
        output = execute(['pep8', '-r', (file.file_path)],
                split_lines=True,
                ignore_errors=True)

        for line in output:
            parsed = line.split(':')
            lnum = int(parsed[1])
            col = int(parsed[2])
            msg = parsed[3]
            file.comment(lnum, 1, 'Col: %s\n%s' % (col, msg))

    review.body_top += "This is a review from Review Bot.\n\n"
    review.body_top += "Tool: pep8\n"
    review.body_top += "\nProcessed Files:\n"
    for file in processed_files:
        review.body_top += "  %s\n" % file

    review.body_top += "\nIgnored Files:\n"
    for file in ignored_files:
        review.body_top += "  %s\n" % file
