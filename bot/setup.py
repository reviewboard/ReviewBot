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
            'flake8 = reviewbot.tools.flake8:Flake8Tool',
            'jshint = reviewbot.tools.jshint:JSHintTool',
            'pmd = reviewbot.tools.pmd:PMDTool',
            'pycodestyle = reviewbot.tools.pycodestyle:PycodestyleTool',
            'pydocstyle = reviewbot.tools.pydocstyle:PydocstyleTool',
            'pyflakes = reviewbot.tools.pyflakes:PyflakesTool',
        ],
    },
    install_requires=[
        'appdirs',
        'celery>=3.0,<4.0',
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
        'Topic :: Software Development',
        'Topic :: Software Development :: Quality Assurance',
    ],
)
