from __future__ import print_function, unicode_literals

import imp
import os

import appdirs


config = {
    'pmd_path': None,
    'checkstyle_path': None,
    'repositories': [],
}


def init():
    """Load the config file."""
    global config

    config_file = os.path.join(appdirs.site_config_dir('reviewbot'),
                               'config.py')

    print('Loading config file %s' % config_file)

    try:
        with open(config_file) as f:
            config_module = imp.load_module('config', f, config_file,
                                            ('py', 'r', imp.PY_SOURCE))

            for key in list(config.keys()):
                if hasattr(config_module, key):
                    value = getattr(config_module, key)
                    config[key] = value
    except:
        print('Unable to load config, using defaults')
