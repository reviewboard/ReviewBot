#!/usr/bin/env python

from setuptools import find_packages, setup

from reviewbot import get_package_version


with open('README.rst', 'r') as fp:
    long_description = fp.read()


setup(
    name='reviewbot-worker',
    version=get_package_version(),
    license='MIT',
    description='Review Bot, the automated code reviewer (worker)',
    long_description=long_description,
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
            'doc8 = reviewbot.tools.doc8:Doc8Tool',
            'fbinfer = reviewbot.tools.fbinfer:FBInferTool',
            'flake8 = reviewbot.tools.flake8:Flake8Tool',
            'jshint = reviewbot.tools.jshint:JSHintTool',
            'pmd = reviewbot.tools.pmd:PMDTool',
            'pycodestyle = reviewbot.tools.pycodestyle:PycodestyleTool',
            'pydocstyle = reviewbot.tools.pydocstyle:PydocstyleTool',
            'pyflakes = reviewbot.tools.pyflakes:PyflakesTool',
            'shellcheck = reviewbot.tools.shellcheck:ShellCheckTool',
        ],
    },
    install_requires=[
        'appdirs',
        'celery>=3.1.25,<4.0; python_version=="2.7"',
        'celery>=4.4,<5.0; python_version>="3.6"',
        'RBTools>=1.0',
    ],
    extras_require={
        'all': [
            'buildbot>=0.8.7',
            'cpplint>=0.0.3',
            'doc8>=0.8.0',
            'flake8>=3.3.0',
            'pycodestyle',
            'pydocstyle',
            'pyflakes',
        ],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Software Development',
        'Topic :: Software Development :: Quality Assurance',
    ],
)
