"""Main command line handler for Review Bot.

Version Added:
    3.0
"""

from __future__ import absolute_import, unicode_literals

import argparse
import os
import socket
import sys

from reviewbot import get_version_string
from reviewbot.celery import get_celery, start_worker


def create_arg_parser():
    """Create an argument parser for Review Bot.

    Version Added:
        3.0

    Returns:
        argparse.ArgumentParser:
        The argument parser for Review Bot.
    """
    celery = get_celery()

    arg_parser = argparse.ArgumentParser(
        description=(
            'Run the Review Bot worker, connecting to a message broker.'
        ))
    arg_parser.add_argument(
        '-v',
        '--version',
        action='version',
        version='Review Bot %s (Python %s)' % (
            get_version_string(),
            '%s.%s' % sys.version_info[:2]))

    arg_parser.add_argument(
        '-b',
        '--broker',
        metavar='BROKER_URL',
        required=True,
        help=(
            'The URL to the message broker. For RabbitMQ, this is in the '
            'form of: amqp://username:password@hostname/reviewbot-vhost'
        )),
    arg_parser.add_argument(
        '-n',
        '--hostname',
        default='reviewbot@%s' % socket.gethostname(),
        help=(
            'A custom hostname to set when communicating with the message '
            'queue. This can be a format string with: %%h (fully-qualified '
            'hostname: name.domain), %%n (name-only part of hostname), '
            '%%d (domain part of hostname)'
        ))

    group = arg_parser.add_argument_group('Logging')
    group.add_argument(
        '-l',
        '--loglevel',
        default='INFO',
        choices=('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', 'FATAL'),
        help='The minimum logging level.')
    group.add_argument(
        '-f',
        '--logfile',
        metavar='PATH',
        help=(
            'The path to the log file to write to. If not specified, all '
            'logging will be to stderr.'
        ))

    group = arg_parser.add_argument_group('Daemonization')
    group.add_argument(
        '-D',
        '--detach',
        action='store_true',
        help=(
            'Detach the worker process, running in the background.'
        ))
    group.add_argument(
        '--pidfile',
        metavar='PATH',
        help=(
            'Path to a file to store the PID of the process. If this file '
            'exists and contains the PID of a running process, Review Bot '
            'will not start.'
        ))
    group.add_argument(
        '--uid',
        help=(
            'The user ID or username to run as after detaching.'
        ))
    group.add_argument(
        '--gid',
        help=(
            'The group ID or name to run as after detaching.'
        ))
    group.add_argument(
        '--umask',
        help=(
            "The effective umask (in octal format) of the process to use "
            "after detaching. By default, the parent process's umask is "
            "used."
        ))

    group = arg_parser.add_argument_group('Message/Process Handling')
    group.add_argument(
        '-c',
        '--concurrency',
        metavar='NUM_PROCESSES',
        type=int,
        default=celery.conf.CELERYD_CONCURRENCY,
        help=(
            'The number of child processes used to process the message '
            'queue. The default is the number of CPUs on your system.'
        ))
    group.add_argument(
        '-P',
        '--pool',
        dest='pool_cls',
        choices=('prefork', 'eventlet', 'gevent', 'solo', 'threads'),
        default=celery.conf.CELERYD_POOL,
        help=(
            'The pool implementation. prefork is the default, and is '
            'recommended.'
        ))
    group.add_argument(
        '--autoscale',
        metavar='MIN,MAX',
        help=(
            'Enable auto-scaling of workers. The value is in the form of '
            'max_concurrency,min_concurrency. For example, --autoscale=10,3 '
            'will keep 3 proceses, but grow to 10 if needed.'
        ))

    return arg_parser


def main(argv=sys.argv[1:]):
    """Run Review Bot.

    Args:
        argv (list):
            All command line arguments passed to Review Bot.
    """
    celery = get_celery()

    if len(argv) > 1 and argv[0] == 'worker':
        # We're running in legacy mode, using 'celery worker' options.
        #
        # We can't use the logger yet, so output straight to sys.stderr.
        sys.stderr.write('WARNING: The "worker" option is deprecated and no '
                         'longer required. Please see reviewbot --help for '
                         'options.\n\n')
        sys.exit(celery.worker_main([sys.argv[0]] + argv[1:]))

    # Now that we're set up, start parsing arguments and then handle them.
    #
    # Ideally, we would just subclass the worker command and take advantage
    # of the patching, the argument parsing, and the invocation of the worker.
    # That'd be great.
    #
    # Unfortunately, the command implementations are a bit of a mess. There
    # are multiple ways to invoke a command, and none of them execute all the
    # same bits of code. For example, as mentioned above, running
    # 'execute_from_commandline()' will happily patch the concurrency module,
    # but won't attempt to handle the detach operation.
    #
    # Even if it did both, the detach operation would end up invoking `celery`
    # and not `reviewbot`.
    #
    # So we bypass all of that, treat the commands as utility classes, and
    # handle all our own parsing and invocation here.
    arg_parser = create_arg_parser()
    options = arg_parser.parse_args(argv)

    sys.exit(start_worker(broker=options.broker,
                          hostname=options.hostname,
                          loglevel=options.loglevel,
                          logfile=options.logfile,
                          detach=options.detach,
                          pidfile=options.pidfile,
                          uid=options.uid,
                          gid=options.gid,
                          umask=options.umask,
                          concurrency=options.concurrency,
                          pool_cls=options.pool_cls,
                          autoscale=options.autoscale))


if __name__ == '__main__':
    main()
