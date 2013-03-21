#!/usr/bin/env python
from setuptools import find_packages, setup


PACKAGE = "reviewbotext"
VERSION = "0.1"

setup(
    name="Review Bot Extension",
    version=VERSION,
    description="An extension for communicating with Review Bot",
    author="Steven MacLeod",
    packages=find_packages(),
    entry_points={
        'reviewboard.extensions':
            '%s = reviewbotext.extension:ReviewBotExtension' % PACKAGE,
    },
    install_requires=[
          'celery',
    ],
    package_data={
        'reviewbotext': [
            'htdocs/css/*.css',
            'htdocs/js/*.js',
            'templates/admin/reviewbotext/reviewbottool/*.html',
            'templates/*.html',
        ],
    }
)
