#!/usr/bin/env python
from setuptools import find_packages, setup

from reviewbot import get_package_version


setup(
    name='reviewbot-worker',
    version=get_package_version(),
    license='MIT',
    description='Review Bot, the automated code reviewer (worker)',
    author='Beanbag, Inc.',
    author_email='support@beanbaginc.com',
    maintainer='Beanbag, Inc.',
    maintainer_email='support@beanbaginc.com',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'reviewbot = reviewbot.celery:main'
        ],
        'reviewbot.tools': [
            'buildbot = reviewbot.tools.buildbot:BuildBotTool',
            'checkstyle = reviewbot.tools.checkstyle:CheckstyleTool',
            'clang = reviewbot.tools.clang:ClangTool',
            'cppcheck = reviewbot.tools.cppcheck:CPPCheckTool',
            'cpplint = reviewbot.tools.cpplint:CPPLintTool',
            'flake8 = reviewbot.tools.flake8:Flake8Tool',
            'jshint = reviewbot.tools.jshint:JSHintTool',
            'pmd = reviewbot.tools.pmd:PMDTool',
            'pycodestyle = reviewbot.tools.pycodestyle:PycodestyleTool',
            'pyflakes = reviewbot.tools.pyflakes:PyflakesTool',
        ],
    },
    install_requires=[
        'appdirs',
        'buildbot>=0.8.7',
        'celery>=3.0,<4.0',
        'cpplint>=0.0.3',
        'flake8>=3.3.0',
        'pycodestyle>=2.3.1',
        'pyflakes>=1.5.0',
        'RBTools>=0.7.10',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development',
    ],
)
