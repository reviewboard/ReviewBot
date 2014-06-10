#!/usr/bin/env python
from setuptools import find_packages, setup

from reviewbot import get_package_version


PACKAGE_NAME = "ReviewBot"


setup(
    name=PACKAGE_NAME,
    version=get_package_version(),
    license="MIT",
    description="ReviewBot, the automated code reviewer",
    author="Steven MacLeod",
    author_email="steven@smacleod.ca",
    maintainer="Steven MacLeod",
    maintainer_email="steven@smacleod.ca",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'reviewbot = reviewbot.celery:main'
        ],
        'reviewbot.tools': [
            'buildbot = reviewbot.tools.buildbot:BuildBotTool',
            'cppcheck = reviewbot.tools.cppcheck:CPPCheckTool',
            'cpplint = reviewbot.tools.cpplint:CPPLintTool',
            'pep8 = reviewbot.tools.pep8:PEP8Tool',
            'pyflakes = reviewbot.tools.pyflakes:PyflakesTool',
        ],
    },
    install_requires=[
        'buildbot>=0.8.7',
        'celery>=3.0',
        'cpplint>=0.0.3',
        'pep8>=0.7.0',
        'pyflakes>=0.5.0',
        'RBTools>=0.6.0',
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Software Development",
    ],
)
