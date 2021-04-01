from __future__ import unicode_literals


#: The version of Review Bot.
#:
#: This is in the format of:
#:
#: (Major, Minor, Micro, Patch, alpha/beta/rc/final, Release Number, Released)
#:
VERSION = (2, 0, 1, 0, 'final', 0, True)


def get_version_string():
    """Return the version of Review Bot.

    Returns:
        unicode:
        The full version.
    """
    version = '%s.%s' % (VERSION[0], VERSION[1])

    if VERSION[2] or VERSION[3]:
        version = '%s.%s' % (version, VERSION[2])

    if VERSION[3]:
        version = '%s.%s' % (version, VERSION[3])

    tag = VERSION[4]

    if tag != 'final':
        if tag == 'rc':
            version = '%s RC%s' % (version, VERSION[5])
        else:
            version = '%s %s %s' % (version, tag, VERSION[5])

    if not is_release():
        version += ' (dev)'

    return version


def get_package_version():
    """Return the package version of Review Bot.

    This is a simplified version string which is used when building a package.

    Returns:
        unicode:
        The version to use for the package.
    """
    version = '%d.%d' % (VERSION[0], VERSION[1])

    if VERSION[2] or VERSION[3]:
        version = '%s.%s' % (version, VERSION[2])

    if VERSION[3]:
        version = '%s.%s' % (version, VERSION[3])

    tag = VERSION[4]

    if tag != 'final':
        if tag == 'alpha':
            tag = 'a'
        elif tag == 'beta':
            tag = 'b'

        version = '%s%s%s' % (version, tag, VERSION[5])

    return version


def is_release():
    """Return whether the current version is a release.

    Returns:
        boolean:
        True if the current version of Review Bot is a released package.
    """
    return VERSION[6]


#: An alias for the the version information from :py:data:`VERSION`.
#:
#: This does not include the last entry in the tuple (the released state).
__version_info__ = VERSION[:-1]

#: An alias for the version used for the Python package.
__version__ = get_package_version()
