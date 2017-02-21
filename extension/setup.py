#!/usr/bin/env python
from setuptools import find_packages
from reviewboard.extensions.packaging import setup

from reviewbotext import get_package_version


setup(
    name='reviewbot-extension',
    version=get_package_version(),
    license='MIT',
    description=('Review Bot, the automated code reviewer (Review Board '
                 'extension)'),
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
        'celery>=3.0,<4.0',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Review Board',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development',
    ],
)
