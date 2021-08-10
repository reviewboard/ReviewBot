#!/usr/bin/env python
from __future__ import unicode_literals

import os
import sys

import nose


def run_tests():
    # Make sure we don't have any environment variables here that
    # could pose problems.
    os.environ.pop(str('REVIEWBOT_CONFIG_FILE'), None)
    os.environ.pop(str('CLASSPATH'), None)

    os.environ['PATH'] = '%s:%s' % (
        os.path.abspath(os.path.join(__file__, '..', 'node_modules', '.bin')),
        os.environ['PATH'])

    nose_argv = [
        'runtests.py',
        '-v',
        '--match=^test',
        '--with-coverage',
        '--cover-package=reviewbot',
    ]

    if len(sys.argv) > 2:
        nose_argv += sys.argv[2:]

    if not nose.run(argv=nose_argv):
        sys.exit(1)


if __name__ == '__main__':
    os.chdir(os.path.join(os.path.dirname(__file__), '..'))
    sys.path.insert(0, os.getcwd())
    run_tests()
