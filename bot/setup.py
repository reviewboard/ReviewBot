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
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'reviewbot = reviewbot.main:main'
        ],
        'reviewbot.tools': [
            'cargotool = reviewbot.tools.cargotool:CargoTool',
            'checkstyle = reviewbot.tools.checkstyle:CheckstyleTool',
            'clang = reviewbot.tools.clang:ClangTool',
            'cppcheck = reviewbot.tools.cppcheck:CPPCheckTool',
            'cpplint = reviewbot.tools.cpplint:CPPLintTool',
            'doc8 = reviewbot.tools.doc8:Doc8Tool',
            'fbinfer = reviewbot.tools.fbinfer:FBInferTool',
            'flake8 = reviewbot.tools.flake8:Flake8Tool',
            'gofmt = reviewbot.tools.gofmt:GofmtTool',
            'gotool = reviewbot.tools.gotool:GoTool',
            'jshint = reviewbot.tools.jshint:JSHintTool',
            'pmd = reviewbot.tools.pmd:PMDTool',
            'pycodestyle = reviewbot.tools.pycodestyle:PycodestyleTool',
            'pydocstyle = reviewbot.tools.pydocstyle:PydocstyleTool',
            'pyflakes = reviewbot.tools.pyflakes:PyflakesTool',
            ('rbsecretscanner = '
             'reviewbot.tools.rbsecretscanner:SecretScannerTool'),
            'rubocop = reviewbot.tools.rubocop:RubocopTool',
            'rustfmt = reviewbot.tools.rustfmt:RustfmtTool',
            'shellcheck = reviewbot.tools.shellcheck:ShellCheckTool',
        ],
    },
    install_requires=[
        'appdirs>=1.4.4',
        'celery>=3.1.25,<4.0; python_version == "2.7"',
        'celery>=5.1.2,<=5.1.999; python_version == "3.6"',
        'celery>=5.2.7,<=5.2.999; python_version >= "3.7"',

        # We have to cap kombu for Python 3.6, as celery 5.1.x covers too
        # broad a range of versions, resulting in a Python 3.6-incompatible
        # kombu to be installed.
        'kombu>=5.1.0,<=5.1.999; python_version == "3.6"',

        'enum; python_version == "2.7"',
        'RBTools>=1.0',

        # We unconditionally include these plugins to ensure they're present.
        'flake8-json>=21.1',
    ],
    extras_require={
        'all': [
            'cpplint>=1.6',
            'doc8>=0.8,<0.8.999; python_version == "2.7"',
            'doc8>=0.10.1; python_version >= "3.6"',
            'flake8>=3.3.0,<3.999; python_version == "2.7"',
            'flake8>=4.0; python_version >= "3.6"',
            'pycodestyle>=2.8',
            'pydocstyle>=3.0,<=3.999; python_version == "2.7"',
            'pydocstyle>=6.1.1; python_version >= "3.6"',
            'pyflakes>=2.4',
        ],
    },
    python_requires=','.join([
        '>=2.7',
        '!=3.0.*',
        '!=3.1.*',
        '!=3.2.*',
        '!=3.3.*',
        '!=3.4.*',
        '!=3.5.*',
    ]),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Framework :: Review Board',
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
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Software Development',
        'Topic :: Software Development :: Quality Assurance',
    ],
)
