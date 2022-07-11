#!/usr/bin/env python

import os
import sys

import reviewboard
from reviewboard.cmdline.rbext import RBExt


def main(argv):
    print('Python %s.%s.%s' % (sys.version_info[:3]))
    print('Review Board %s' % reviewboard.get_version_string())

    # When we drop Review Board 3.x support, we can remove -s and -m and
    # switch to:
    #
    #     -e reviewbotext.extension.ReviewBotExtension
    sys.exit(RBExt().run([
        'test',
        '-s', os.path.abspath(os.path.join(__file__, '..',
                                           'settings_local.py')),
        '-m', 'reviewbotext',
        '--',
    ] + argv))


if __name__ == '__main__':
    main(sys.argv[1:])
