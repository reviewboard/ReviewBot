#!/usr/bin/env python
from setuptools import find_packages
from reviewboard.extensions.packaging import setup

from reviewbotext import get_package_version


PACKAGE = "reviewbotext"


setup(
    name="Review Bot Extension",
    version=get_package_version(),
    description="An extension for communicating with Review Bot",
    author="Steven MacLeod",
    include_package_data=True,
    packages=find_packages(),
    entry_points={
        'reviewboard.extensions':
            '%s = reviewbotext.extension:ReviewBotExtension' % PACKAGE,
    },
    install_requires=[
          'celery',
    ],
)
