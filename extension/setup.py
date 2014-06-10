#!/usr/bin/env python
from setuptools import find_packages
from reviewboard.extensions.packaging import setup

from reviewbotext import get_package_version


PACKAGE = "reviewbotext"


setup(
    name="Review Bot Extension",
    version=get_package_version(),
    license="MIT",
    description="A Review Board extension for communicating with Review Bot",
    author="Steven MacLeod",
    maintainer="Steven MacLeod",
    include_package_data=True,
    packages=find_packages(),
    entry_points={
        'reviewboard.extensions':
            'reviewbot = reviewbotext.extension:ReviewBotExtension',
    },
    install_requires=[
          'celery>=3.0',
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Software Development",
    ],
)
