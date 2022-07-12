#!/usr/bin/env python

from reviewboard.extensions.packaging import setup
from setuptools import find_packages

from reviewbotext import get_package_version


with open('README.rst', 'r') as fp:
    long_description = fp.read()


setup(
    name='reviewbot-extension',
    version=get_package_version(),
    license='MIT',
    description=('Review Bot, the automated code reviewer (Review Board '
                 'extension)'),
    long_description=long_description,
    author='Beanbag, Inc.',
    author_email='support@beanbaginc.com',
    maintainer='Beanbag, Inc.',
    maintainer_email='support@beanbaginc.com',
    include_package_data=True,
    packages=find_packages(),
    entry_points={
        'reviewboard.extensions':
            'reviewbot = reviewbotext.extension:ReviewBotExtension',
    },
    install_requires=[
        'celery>=3.1.25,<4.0; python_version == "2.7"',
        'celery>=5.1.2,<=5.1.999; python_version == "3.6"',
        'celery>=5.2.7,<=5.2.999; python_version >= "3.7"',

        # We have to cap kombu for Python 3.6, as celery 5.1.x covers too
        # broad a range of versions, resulting in a Python 3.6-incompatible
        # kombu to be installed.
        'kombu>=5.1.0,<=5.1.999; python_version == "3.6"',

        'six',
    ],
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
        'Environment :: Web Environment',
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
