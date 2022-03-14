"""Configuration loading and validation."""

from __future__ import print_function, unicode_literals

import json
import os
from copy import deepcopy
from glob import glob

import six
from appdirs import AppDirs

from reviewbot.utils.log import get_root_logger


logger = get_root_logger()

_appdirs = AppDirs(appname='reviewbot',
                   appauthor='Beanbag')


#: The default configuration for Review Bot.
#:
#: :py:data:`config` is generated from this.
#:
#: Version Added:
#:     3.0
DEFAULT_CONFIG = {
    'cookie_dir': _appdirs.user_cache_dir,
    'exe_paths': {},
    'java_classpaths': {},
    'reviewboard_servers_config_path': None,
    'reviewboard_servers': [],
    'repositories_config_path': None,
    'repositories': [],
}

#: Deprecated configuration keys.
#:
#: Version Added:
#:     3.0
deprecated_keys = {
    'pmd_path',
    'review_board_servers',
}


#: The active configuration for Review Bot.
config = deepcopy(DEFAULT_CONFIG)


def _load_json_config_items(path):
    """Load items from a JSON configuration file.

    Version Added:
        3.0

    Args:
        path (unicode):
            The path to the file.

    Returns:
        list:
        The resulting list of items.
    """
    try:
        with open(path, 'r') as fp:
            items = json.load(fp)
    except IOError as e:
        logger.warning('Unable to read the configuration file "%s": %s',
                       path, e)
        return []

    if not isinstance(items, list):
        logger.error('The configuration file at %s must contain a list, not '
                     'a %s.',
                     path, type(items).__name__)
        return []

    return items


def get_config_file_path():
    """Return the configuration file path.

    Version Added:
        3.0

    Returns:
        unicode:
        The configuration file path.
    """
    return os.environ.get(
        str('REVIEWBOT_CONFIG_FILE'),
        os.path.join(_appdirs.site_config_dir, 'config.py'))


def load_config():
    """Load the Review Bot configuraiton.

    This will load the configuration file :file:`reviewbot/config.py`,
    located in the system's main configuration directory (:file:`/etc/` on
    Linux).

    If the :envvar:`REVIEWBOT_CONFIG_FILE` environment variable is provided,
    configuration from that file will be loaded instead.

    If anything goes wrong when loading the configuration, the defaults will
    be used.

    Version Added:
        3.0:
        This was previously called ``init``. As it's internal API, hopefully
        nobody was calling that.
    """
    global config

    config_file = get_config_file_path()

    # We're going to work on a copy of this and set it only at the end, in
    # the event that we're sharing state with other threads.
    new_config = deepcopy(DEFAULT_CONFIG)

    if os.path.exists(config_file):
        logger.info('Loading Review Bot configuration file %s', config_file)

        try:
            with open(config_file, 'r') as f:
                config_module = {}
                exec(compile(f.read(), config_file, 'exec'), config_module)

            for key in six.iterkeys(DEFAULT_CONFIG):
                if key in config_module:
                    new_config[key] = deepcopy(config_module[key])

            if 'checkstyle_path' in config_module:
                logger.warning('checkstyle_path in %s is deprecated and will '
                               'be removed in Review Bot 4.0. Please put '
                               'this in "java_classpaths". For example:\n'
                               'java_classpaths = {\n'
                               '    "checkstyle": ["%s"],\n'
                               '}',
                               config_file, config_module['checkstyle_path'])

                new_config['java_classpaths']['checkstyle'] = [
                    config_module['checkstyle_path'],
                ]

            if 'pmd_path' in config_module:
                logger.warning('pmd_path in %s is deprecated and will be '
                               'removed in Review Bot 4.0. Please put '
                               'this in "exe_paths". For example:\n'
                               'exe_paths = {\n'
                               '    "pmd": "%s",\n'
                               '}',
                               config_file, config_module['pmd_path'])

                new_config['exe_paths']['pmd'] = config_module['pmd_path']

            if 'review_board_servers' in config_module:
                logger.warning('review_board_servers in %s is '
                               'deprecated and will be removed in '
                               'Review Bot 4.0. Please rename it to '
                               'reviewboard_servers or set '
                               'reviewboard_servers_config_path to the '
                               'location of a JSON file.',
                               config_file)

                new_config['reviewboard_servers'] = \
                    config_module['review_board_servers']
        except IOError as e:
            logger.error('Unable to read the Review Bot configuration '
                         'file: %s',
                         e)
        except Exception as e:
            logger.error('Error loading Review Bot configuration file: %s',
                         e,
                         exc_info=True)
    else:
        logger.warning('Configuration was not found at %s. Using the '
                       'defaults.',
                       config_file)

    # If a Review Board servers JSON file was specified, load it into the
    # configuration.
    servers_path = new_config['reviewboard_servers_config_path']

    if servers_path:
        if os.path.exists(servers_path):
            new_config['reviewboard_servers'] += \
                _load_json_config_items(servers_path)
        else:
            logger.warning('The Review Board servers configuration file "%s" '
                           'was not found. If you aren\'t using tools that '
                           'require full-repository access, you can ignore '
                           'this.',
                           servers_path)

    # If a repositories JSON file was specified, load it into the
    # configuration.
    repositories_config_path = new_config['repositories_config_path']

    if repositories_config_path:
        if os.path.exists(repositories_config_path):
            new_config['repositories'] += \
                _load_json_config_items(repositories_config_path)
        else:
            logger.warning('The repository configuration file "%s" was not '
                           'found. If you aren\'t using tools that require '
                           'full-repository access, you can ignore this.',
                           repositories_config_path)

    # Ensure some settings are set to sane values.
    cookie_dir = new_config['cookie_dir']

    if not cookie_dir:
        logger.error('cookie_dir was empty in %s. Using the default '
                     'of %s instead.',
                     config_file,
                     DEFAULT_CONFIG['cookie_dir'])
        cookie_dir = DEFAULT_CONFIG['cookie_dir']
        new_config['cookie_dir'] = cookie_dir
    elif not os.path.isabs(cookie_dir):
        logger.error('cookie_dir (%s) must be a relative path in %s. '
                     'Using the default of %s instead.',
                     cookie_dir,
                     config_file,
                     DEFAULT_CONFIG['cookie_dir'])
        cookie_dir = DEFAULT_CONFIG['cookie_dir']
        new_config['cookie_dir'] = cookie_dir

    # Set the full cookie path, for convenience. This setting cannot be
    # customized.
    new_config['cookie_path'] = os.path.join(cookie_dir,
                                             'reviewbot-cookies.txt')

    config.clear()
    config.update(new_config)


def reset_config():
    """Reset the configuration to defaults.

    Version Added:
        3.0
    """
    config.clear()
    config.update(deepcopy(DEFAULT_CONFIG))
