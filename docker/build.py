#!/usr/bin/env python
"""Builds a Docker image for the current version of Review Bot."""

from __future__ import print_function, unicode_literals

import argparse
import os
import subprocess
import sys

docker_dir = os.path.dirname(__file__)
sys.path.insert(0, os.path.abspath(os.path.join(docker_dir, '..', '..',
                                                'bot')))

from reviewbot import VERSION, get_package_version, is_release


IMAGE_FMT = 'beanbag/reviewbot-%s'
IMAGES = [
    'base',
    'c',
    'fbinfer',
    'go',
    'java',
    'javascript',
    'pmd',
    'python',
    'ruby',
    'rust',
    'shell',
]

ARCHS = [
    'linux/amd64',
]


if __name__ == '__main__':
    argparser = argparse.ArgumentParser(
        description='Build and optionally upload the Docker image.')
    argparser.add_argument(
        '--latest',
        dest='tag_latest',
        action='store_true',
        help='whether to tag with "latest" (should only be used if '
             'this is the very latest public version of Review Bot.')
    argparser.add_argument(
        '--no-major',
        action='store_false',
        dest='tag_major',
        help='disable tagging the image with the "X" major version tag')
    argparser.add_argument(
        '--no-major-minor',
        action='store_false',
        dest='tag_major_minor',
        help='disable tagging the image with the "X.Y" major.minor version '
             'tag')
    argparser.add_argument(
        '--upload',
        action='store_true',
        help='upload the image after build')

    options = argparser.parse_args()

    package_version = get_package_version()
    major_version = '%s' % VERSION[0]
    major_minor_version = '%s.%s' % VERSION[:2]
    image_version = package_version

    # If this is a development release, check if a built package has been
    # placed in the packages/ directory.
    if not is_release():
        package_version = '%s.dev0' % package_version
        package_path = os.path.join(docker_dir, 'base', 'packages',
                                    'reviewbot_worker-%s-py2.py3-none-any.whl'
                                    % package_version)

        if not os.path.exists(package_path):
            sys.stderr.write(
                'To build a Docker image for an in-development '
                'version of Review Bot, you will\n'
                'need to build a development package and place it at:\n'
                '\n'
                '%s\n'
                % package_path)
            sys.exit(1)

    base_image = IMAGE_FMT % 'base'

    build_args = [
        '--platform', ','.join(ARCHS),
        '--build-arg', 'REVIEWBOT_VERSION=%s' % package_version,
        '--build-arg', 'REVIEWBOT_BASE_TAG=%s:%s' % (base_image,
                                                     image_version),
    ]

    all_tags = []

    for image in IMAGES:
        image_name = IMAGE_FMT % image
        tags = ['%s:%s' % (image_name, image_version)]

        if options.tag_major:
            tags.append('%s:%s' % (image_name, major_version))

        if options.tag_major_minor:
            tags.append('%s:%s' % (image_name, major_minor_version))

        if options.tag_latest:
            tags.append(image_name)

        all_tags += tags

        # Build the Docker command line to run.
        cmd = ['docker', 'build'] + build_args

        for tag in tags:
            cmd += ['-t', tag]

        cmd.append('.')

        # Now build the image.
        print('===== Building %s =====' % image_name)
        p = subprocess.Popen(cmd,
                             stdout=sys.stdout,
                             stderr=sys.stderr,
                             cwd=os.path.join(docker_dir, image))

        if p.wait() != 0:
            sys.exit(1)

        print()

    if options.upload:
        for tag in all_tags:
            p = subprocess.Popen(['docker', 'push', tag],
                                 stdout=sys.stdout,
                                 stderr=sys.stderr,
                                 cwd=docker_dir)

            if p.wait() != 0:
                sys.exit(1)
