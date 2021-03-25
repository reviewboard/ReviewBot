from __future__ import print_function, unicode_literals

import logging
import os
from copy import deepcopy

import appdirs
import six


logger = logging.getLogger(__name__)


#: The default configuration for Review Bot.
#:
#: :py:data:`config` is generated from this.
#:
#: Version Added:
#:     3.0
DEFAULT_CONFIG = {
    'exe_paths': {},
    'reviewboard_servers': [],
    'repositories': [],
}

#: Deprecated configuration keys.
#:
#: Version Added:
#:     3.0
deprecated_keys = {
    'review_board_servers',
}


#: The active configuration for Review Bot.
config = deepcopy(DEFAULT_CONFIG)


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

    config_file = os.environ.get(
        str('REVIEWBOT_CONFIG_FILE'),
        os.path.join(appdirs.site_config_dir('reviewbot'), 'config.py'))

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

            if 'review_board_servers' in config_module:
                logger.warning('review_board_servers in %s is '
                               'deprecated and will be removed in '
                               'Review Bot 4.0. Please rename it to '
                               'reviewboard_servers.',
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
        logger.warning('Review Bot configuration was not found at %s. '
                       'Using the defaults.',
                       config_file)

    config.clear()
    config.update(new_config)


def reset_config():
    """Reset the configuration to defaults.

    Version Added:
        3.0
    """
    config.clear()
    config.update(deepcopy(DEFAULT_CONFIG))
