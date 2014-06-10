#!/usr/bin/env python
from setuptools import find_packages, setup


VERSION = "1.0"

setup(
    name="ReviewBotExtension",
    version=VERSION,
    license="MIT",
    description="A Review Board extension for communicating with Review Bot",
    author="Steven MacLeod",
    author_email="steven@smacleod.ca",
    maintainer="Steven MacLeod",
    maintainer_email="steven@smacleod.ca",
    packages=find_packages(),
    entry_points={
        'reviewboard.extensions':
            'reviewbot = reviewbotext.extension:ReviewBotExtension',
    },
    install_requires=[
          'celery>=3.0',
    ],
    package_data={
        'reviewbotext': [
            'htdocs/css/*.css',
            'htdocs/js/*.js',
            'templates/admin/reviewbotext/tool/*.html',
            'templates/*.html',
        ],
    },
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
