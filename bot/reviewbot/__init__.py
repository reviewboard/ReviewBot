from __future__ import unicode_literals


# The version of Review Bot.
#
# This is in the format of:
#
#   (Major, Minor, Micro, alpha/beta/rc/final, Release Number, Released)
#
VERSION = (1, 0, 1, 'final', 0, True)


def get_version_string():
    """Return the version of Review Bot.

    Returns:
        unicode:
        The full version.
    """
    version = '%s.%s' % (VERSION[0], VERSION[1])

    if VERSION[2]:
        version += ".%s" % VERSION[2]

    if VERSION[3] != 'final':
        if VERSION[3] == 'rc':
            version += ' RC%s' % VERSION[4]
        else:
            version += ' %s %s' % (VERSION[3], VERSION[4])

    if not is_release():
        version += " (dev)"

    return version


def get_package_version():
    """Return the package version of Review Bot.

    This is a simplified version string which is used when building a package.

    Returns:
        unicode:
        The version to use for the package.
    """
    version = '%d.%d' % (VERSION[0], VERSION[1])

    if VERSION[2]:
        version += ".%d" % VERSION[2]

    if VERSION[3] != 'final':
        version += '%s%d' % (VERSION[3], VERSION[4])

    return version


def is_release():
    """Return whether the current version is a release.

    Returns:
        boolean:
        True if the current version of Review Bot is a released package.
    """
    return VERSION[5]


__version_info__ = VERSION[:-1]
__version__ = get_package_version()
